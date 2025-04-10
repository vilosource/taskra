from .base import BaseService

class PermissionsService(BaseService):
    """Service for checking Jira user permissions."""

    def get_permissions(self):
        """
        Fetch current user's permissions.

        Returns:
            dict: Permissions response from Jira
        """
        return self.client.get("/rest/api/3/mypermissions")

    def has_required_permissions(self, required=None):
        """
        Check if user has all required permissions.

        Args:
            required (list): List of permission keys to check

        Returns:
            tuple: (bool, list of missing permissions)
        """
        if required is None:
            required = [
                "BROWSE_PROJECTS",
                "CREATE_ISSUES",
                "EDIT_ISSUES",
                "WORK_ON_ISSUES",
                "ADD_COMMENTS"
            ]
        permissions_data = self.get_permissions()
        permissions = permissions_data.get("permissions", {})
        missing = []
        for key in required:
            perm = permissions.get(key)
            if not perm or not perm.get("havePermission"):
                missing.append(key)
        return (len(missing) == 0, missing)
