# from components.rights.load import load_rights
#
# for premis_rights in fsentry.get_premis_rights():
#     load_rights(premis_rights)
#

from metsrw.plugins import premisrw
import pytest
import uuid

from components.rights import load
from main.models import File, Transfer, SIP, MetadataAppliesToType


@pytest.fixture()
def rights_statement():
    return premisrw.PREMISRights(data=(
        "rights_statement",
        premisrw.PREMIS_META,
        (
            "rights_statement_identifier",
            ("rights_statement_identifier_type", "UUID"),
            ("rights_statement_identifier_value", "3a9838ac-ebe9-4ecb-ba46-c31ee1d6e7c2"),
        ),
        ("rights_basis", "Copyright"),
        (
            "rights_granted",
            ("act", "Disseminate"),
            ("restriction", "Allow"),
            (
                "term_of_grant",
                ("start_date", "2000"),
                ("end_date", "OPEN"),
            ),
            ("rights_granted_note", "Attribution required"),
        ),
        (
            "rights_granted",
            ("act", "Access"),
            ("restriction", "Allow"),
            (
                "term_of_grant",
                ("start_date", "1999"),
                ("end_date", "OPEN"),
            ),
            ("rights_granted_note", "Access one year before dissemination"),
        ),
        (
            "linking_object_identifier",
            ("linking_object_identifier_type", "UUID"),
            ("linking_object_identifier_value", "c09903c4-bc29-4db4-92da-47355eec752f"),
        ),
    ))


@pytest.fixture()
def file(db):
    return File.objects.create(uuid=uuid.uuid4())


@pytest.mark.django_db
def test_mdtype():
    assert isinstance(load._mdtype(File()), MetadataAppliesToType)
    assert isinstance(load._mdtype(Transfer()), MetadataAppliesToType)
    assert isinstance(load._mdtype(SIP()), MetadataAppliesToType)

    class UnknownClass(object):
        pass

    with pytest.raises(TypeError) as excinfo:
        load._mdtype(UnknownClass())
    assert "Types supported: File, Transfer, SIP" in str(excinfo.value)


@pytest.mark.django_db
def test_load_rights(file, rights_statement):
    stmt = load.load_rights(file, rights_statement)
    assert stmt.metadataappliestotype.description == "File"
    assert stmt.metadataappliestoidentifier == file.uuid
    assert stmt.rightsstatementidentifiertype == "UUID"
    assert stmt.rightsstatementidentifiervalue == "3a9838ac-ebe9-4ecb-ba46-c31ee1d6e7c2"
    assert stmt.rightsbasis == "Copyright"
    rights_granted = stmt.rightsstatementrightsgranted_set.all()
    assert rights_granted[0].act == "Disseminate"
    # TODO assert rights_granted[0].notes.all()[0].rightsgrantednote == "Attribution required"
