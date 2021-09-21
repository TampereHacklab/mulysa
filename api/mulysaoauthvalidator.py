from oauth2_provider.oauth2_validators import OAuth2Validator


class MulysaOAuth2Validator(OAuth2Validator):
    """
    For providing more data to keycloack
    """

    """
    Parse localpart from mxid

    We are trusting that the format is valid
    """
    def _getMxIDLocalPart(mxid):
        if(mxid):
            return mxid.split(':')[0][1:]
        return ""

    def get_additional_claims(self, request):
        """
        give email, firstname and lastname in oid claims data
        """
        return {
            "sub": request.user.email,
            "email": request.user.email,
            "firstName": request.user.first_name,
            "lastName": request.user.last_name,
            "mxid_local_part": self._getMxIDLocalPart(request.user.mxid),
            "mxid_full": request.user.mxid,
        }
