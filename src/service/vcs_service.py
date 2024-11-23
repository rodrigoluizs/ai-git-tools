from abc import abstractmethod, ABC


class VcsService(ABC):
    def __init__(self):
        self.validate_environment()

    @abstractmethod
    def validate_environment(self):
        """
        Perform service-specific environment validations, such as checking for required tokens.
        """
        pass

    @abstractmethod
    def get_username(self):
        """
        Retrieve the username of the user for the specific service.
        """
        pass

    @abstractmethod
    def create_pull_request(self, branch_name, pr_title, pr_body):
        """
        Create a pull request for the specific service.
        """
        pass
