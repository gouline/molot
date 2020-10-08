import jinja2
import boto3
import logging

import molot
from molot.context import Context
from molot.installer import install
install([
    'boto3',
    ('jinja2', 'Jinja2')
])


class CloudFormationContext(Context):
    """CloudFormation wrapper context.
    """

    def __init__(self, stack_name: str, parameters: dict,
                 template_body='', template_path='', template_args={},
                 capabilities=[], wait=True):
        """Creates new instance of context.

        Arguments:
            stack_name {str} -- Name of stack to operate on.
            parameters {dict} -- Template parameters (only required ones will be used).

        Keyword Arguments:
            template_body {str} -- Template body (conflicts with template_path and template_args). (default:{''})
            template_path {str} -- Path to template file (conflicts with template_body). (default:{''})
            template_args {dict} -- Template arguments, when non-empty template treated as Jinja2 template and rendered. (default:{{}})
            capabilities {list} -- List of CloudFormation capabilities required. {(default: {[]})}
            wait {bool} -- When true, stack operations will wait for completion. (default: {True})
        """

        self.stack_name = stack_name
        self.parameters = parameters
        self.capabilities = capabilities
        self.wait = wait
        self.client = boto3.client('cloudformation')

        if template_body:
            self.template_body = template_body
        elif template_path:
            with open(template_path, 'r') as f:
                self.template_body = f.read()

            if template_args:
                self.template_body = jinja2.Template(
                    self.template_body).render(**template_args)

        if self.template_body:
            validation = self.client.validate_template(
                TemplateBody=self.template_body
            )
            keys = [x['ParameterKey'] for x in validation['Parameters']]

            self.template_parameters = list()
            for key in self.parameters:
                if key in keys:
                    self.template_parameters.append({
                        'ParameterKey': key,
                        'ParameterValue': self.parameters[key]
                    })

    def describe_stack(self) -> dict:
        """Describes current stack, if it exists.

        Returns:
            dict -- Stack properties.
        """

        try:
            response = self.client.describe_stacks(
                StackName=self.stack_name
            )
        except self.client.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if "does not exist" in error_message:
                return None

        stacks = response['Stacks']
        if len(stacks) == 1:
            return stacks[0]
        return stacks

    def create_stack(self):
        """Creates stack based on parameters.
        """

        logging.info("Creating stack %s", self.stack_name)
        resp = self.client.create_stack(
            StackName=self.stack_name,
            TemplateBody=self.template_body,
            Parameters=self.template_parameters,
            Capabilities=self.capabilities
        )
        logging.info(resp)
        self._start_wait('create')

    def update_stack(self):
        """Updates existing stack based on parameters.
        """

        try:
            logging.info("Updating stack %s", self.stack_name)
            resp = self.client.update_stack(
                StackName=self.stack_name,
                TemplateBody=self.template_body,
                Parameters=self.template_parameters,
                Capabilities=self.capabilities
            )
            logging.info(resp)
            self._start_wait('update')
        except self.client.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if "No updates are to be performed" in error_message:
                logging.info(error_message)
            else:
                raise

    def upsert_stack(self):
        """Creates stack if it doesn't exist, otherwise updates existing.
        """

        try:
            self.create_stack()
            return
        except self.client.exceptions.AlreadyExistsException:
            logging.info("Stack %s already exists", self.stack_name)

        self.update_stack()

    def delete_stack(self):
        """Deletes existing stack based on parameters.
        """

        resp = self.client.delete_stack(StackName=self.stack_name)
        logging.info(resp)

    def _start_wait(self, action):
        if self.wait:
            logging.info("Waiting for stack %s to %s", self.stack_name, action)
            waiter = self.client.get_waiter(f"stack_{action}_complete")
            waiter.wait(StackName=self.stack_name)
            logging.info("Finished waiting for stack %s to %s",
                         self.stack_name, action)
