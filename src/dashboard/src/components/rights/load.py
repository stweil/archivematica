"""Import ``PREMISRights``.

Similar to ``rights_from_csv`` in that it imports rights statements. In this
module, we load a ``premisrw.PREMISRights`` object into the database.
"""

from __future__ import unicode_literals

import six

from components.helpers import get_metadata_type_id_by_description
from main.models import (
    File, Transfer, SIP,
    RightsStatement,
    RightsStatementCopyright,
    RightsStatementCopyrightDocumentationIdentifier,
    RightsStatementCopyrightNote,
    RightsStatementLicense,
    RightsStatementLicenseDocumentationIdentifier,
    RightsStatementLicenseNote,
    RightsStatementRightsGranted,
    RightsStatementRightsGrantedNote,
    RightsStatementRightsGrantedRestriction,
    RightsStatementStatuteInformation,
    RightsStatementStatuteInformationNote,
    RightsStatementStatuteDocumentationIdentifier,
    RightsStatementOtherRightsInformation,
    RightsStatementOtherRightsDocumentationIdentifier,
    RightsStatementOtherRightsInformationNote,
    RightsStatementLinkingAgentIdentifier,
)


_ALLOWED_METADATA_TYPES = (File, Transfer, SIP)


def _mdtype(obj):
    """Return the ``MetadataAppliesToType`` that corresponds to ``obj.``."""
    if obj.__class__ not in _ALLOWED_METADATA_TYPES:
        raise TypeError("Types supported: %s" % ", ".join([item.__name__ for item in _ALLOWED_METADATA_TYPES]))
    return get_metadata_type_id_by_description(obj.__class__.__name__)


def _create_rights_granted(stmt, rights_granted):
    granted = RightsStatementRightsGranted.objects.create(rightsstatement=stmt)
    if rights_granted.act:
        granted.act = rights_granted.act
    for item in rights_granted.restriction:
        pass  # TODO
    # TODO - <xs:element ref="termOfGrant" minOccurs="0"/>
    # TODO - <xs:element ref="termOfRestriction" minOccurs="0"/>
    # TODO notes? lists too?
    if isinstance(rights_granted.rights_granted_note, six.string_types):
        RightsStatementRightsGrantedNote.objects.create(
            rightsgranted=granted, rightsgrantednote=rights_granted.rights_granted_note)
    else:
        for item in rights_granted.rights_granted_note:
            RightsStatementRightsGrantedNote.objects.create(
                rightsgranted=granted, rightsgrantednote=item)
    granted.save()
    return granted


def _create_rights_statement(md_type, obj_id, rights_statement):
    stmt = RightsStatement.objects.create(
        metadataappliestotype=md_type,
        metadataappliestoidentifier=obj_id,
        status="ORIGINAL"
    )

    if rights_statement.rights_statement_identifier_type and rights_statement.rights_statement_identifier_value:
        stmt.rightsstatementidentifiertype = rights_statement.rights_statement_identifier_type
        stmt.rightsstatementidentifiervalue = rights_statement.rights_statement_identifier_value

    if rights_statement.rights_basis:
        stmt.rightsbasis = basis = rights_statement.rights_basis

    if basis == "Copyright":
        # - copyright_information
        pass
    elif basis == "License":
        # - license_information
        pass
    elif basis == "Statute":
        # - statute_information
        pass
    elif basis in ("Donor", "Policy", "Other"):
        # - other_rights_information
        pass

    for item in rights_statement.rights_granted:
        _create_rights_granted(stmt, item)

    # stmt.save()
    return stmt


def load_rights(obj, rights_statement):
    return _create_rights_statement(_mdtype(obj), obj.uuid, rights_statement)
