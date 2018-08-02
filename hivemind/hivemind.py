
import re
import time
from itertools import combinations

from helpers.ipfshelpers import IPFSDict, IPFSDictChain
from helpers.loghelpers import LOG
from validators.validators import valid_address, valid_bech32_address
from taghash.taghash import TagHash
from inputs.inputs import get_sil
from linker.linker import get_lal
from sign_message import verify_message


class HivemindIssue(IPFSDict):
    def __init__(self, multihash=None):
        """
        Constructor of Hivemind issue class

        :param multihash: The ipfs multihash of the hivemind issue
        """
        self.hivemind_id = None
        self.questions = []
        self.description = ''
        self.tags = None
        self.answer_type = u'String'
        self.consensus_type = u'Single'  # Single or Ranked: Is the expected result of this question a single answer or a ranked list?
        self.constraints = None
        self.restrictions = None

        # What happens when an option is selected: valid values are None, Finalize, Exclude, Reset
        # None : nothing happens
        # Finalize : Hivemind is finalized, no new options or opinions can be added anymore
        # Exclude : The selected option is excluded from the results
        # Reset : All opinions are reset
        self.on_selection = None

        super(HivemindIssue, self).__init__(multihash=multihash)

    def add_question(self, question):
        if isinstance(question, (str, unicode)) and question not in self.questions:
            self.questions.append(unicode(question))

    def set_description(self, description):
        if isinstance(description, (str, unicode)):
            self.description = unicode(description)

    def set_tags(self, tags):
        if isinstance(tags, (str, unicode)):
            self.tags = unicode(tags)

    def set_answer_type(self, answer_type):
        if answer_type in ['String', 'Bool', 'Integer', 'Float', 'Hivemind', 'Image', 'Video', 'Complex', 'Address']:
            self.answer_type = unicode(answer_type)
        else:
            raise Exception('Invalid answer_type: %s (must be one of the following: "String", "Bool", "Integer", "Float", "Hivemind", "Image", "Video", "Complex", "Address")' % answer_type)

    def set_consensus_type(self, consensus_type):
        if consensus_type in ['Single', 'Ranked']:
            self.consensus_type = unicode(consensus_type)
        else:
            raise Exception('Consensus_type must be either Single or Ranked, got %s' % consensus_type)

    def set_constraints(self, constraints):
        if not isinstance(constraints, dict):
            raise Exception('constraints must be a dict, got %s' % type(constraints))

        if 'specs' in constraints:
            specs = constraints['specs']
            if not isinstance(constraints['specs'], dict):
                raise Exception('constraint "specs" must be a dict, got %s' % type(specs))

            for key in specs:
                if specs[key] not in ['String', 'Integer', 'Float']:
                    raise Exception('Spec type must be String or Integer or Float, got %s' % specs[key])

        for constraint_type in ['min_length', 'max_length', 'min_value', 'max_value', 'decimals']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], (int, float, long)):
                raise Exception('Value of constraint %s must be a number' % constraint_type)

        for constraint_type in ['regex']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], (str, unicode)):
                raise Exception('Value of constraint %s must be a string' % constraint_type)

        for constraint_type in ['choices']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], list):
                raise Exception('Value of constraint %s must be a list' % constraint_type)

        for constraint_type in ['SIL', 'LAL']:
            if constraint_type in constraints and not (valid_address(constraints[constraint_type]) or valid_bech32_address(constraints[constraint_type])):
                raise Exception('Value of constraint %s must be a valid address' % constraint_type)

        if 'LAL' in constraints and 'xpub' not in constraints:
            raise Exception('Constraints that include a LAL must also have a xpub specified!')

        for constraint_type in ['block_height']:
            if constraint_type in constraints and not isinstance(constraints[constraint_type], (int, long)):
                raise Exception('Value of constraint %s must be a integer' % constraint_type)

        if all([key in ['min_length', 'max_length', 'min_value', 'max_value', 'decimals', 'regex', 'specs', 'choices', 'SIL', 'LAL', 'xpub', 'block_height'] for key in constraints.keys()]):
            self.constraints = constraints
        else:
            raise Exception('constraints contain an invalid key: %s' % constraints)

    def set_restrictions(self, restrictions):
        if not isinstance(restrictions, dict):
            raise Exception('Restrictions is not a dict , got %s instead' % type(restrictions))

        for key in restrictions.keys():
            if key not in ['addresses', 'options_per_address']:
                raise Exception('Invalid key in restrictions: %s' % key)

        if 'addresses' in restrictions:
            if not isinstance(restrictions['addresses'], list):
                raise Exception('addresses in restrictions must be a list, got %s instead' % type(restrictions['addresses']))

            for address in restrictions['addresses']:
                if not (valid_address(address=address) or valid_bech32_address(address=address)):
                    raise Exception('Address %s in restrictions is not valid!' % address)

        if 'options_per_address' in restrictions:
            if not isinstance(restrictions['options_per_address'], int) or restrictions['options_per_address'] < 1:
                raise Exception('options per address in restrictions is invalid: %s' % restrictions['options_per_address'])

        self.restrictions = restrictions

    def set_on_selection(self, on_selection):
        if on_selection not in [None, 'Finalize', 'Exclude', 'Reset']:
            raise Exception('Invalid value for on_selection: %s' % on_selection)

        self.on_selection = unicode(on_selection)

    def id(self):
        taghash = TagHash(tags=self.questions[0])
        taghash.add_tag(tag=self.answer_type)
        if self.tags is not None:
            taghash.add_tag(tag=self.tags)

        self.hivemind_id = unicode(taghash.get())
        return self.hivemind_id

    def info(self):
        """
        Get info about the hivemind question

        :return: A string containing info about the hivemind question
        """
        info = 'Hivemind ID: %s\n' % self.hivemind_id
        info += 'Hivemind question: %s\n' % self.questions[0]
        info += 'Hivemind description: %s\n' % self.description
        info += 'Hivemind tags: %s\n' % self.tags
        info += 'Answer type: %s\n' % self.answer_type

        for constraint_type, constraint_value in self.constraints.items():
            info += 'Constraint %s: %s\n' % (constraint_type, constraint_value)

        for i, additional_question in enumerate(self.questions[1:]):
            info += 'Additional question %s: %s\n' % (i + 1, additional_question)

        return info

    def save(self):
        self.hivemind_id = self.id()
        return super(HivemindIssue, self).save()


class HivemindOption(IPFSDict):
    def __init__(self, multihash=None):
        """
        Constructor of the Option object

        :param multihash: The IPFS multihash of the Option (optional)
        """
        self.hivemind_issue_hash = None
        self._hivemind_issue = None  # set as a private member because it is not json encodable and members of an IPFSDict starting with '_' are ignored when saving

        self.value = None
        self.answer_type = None  # can be 'String', 'Bool', 'Integer', 'Float', 'Hivemind', 'Image', 'Video', 'Complex', 'Address'

        super(HivemindOption, self).__init__(multihash=multihash)

    def load(self, multihash):
        super(HivemindOption, self).load(multihash=multihash)
        self.set_hivemind_issue(hivemind_issue_hash=self.hivemind_issue_hash)

    def set_hivemind_issue(self, hivemind_issue_hash):
        self.hivemind_issue_hash = hivemind_issue_hash
        self._hivemind_issue = HivemindIssue(multihash=self.hivemind_issue_hash)
        self.answer_type = self._hivemind_issue.answer_type

    def set(self, value):
        self.value = value

        if not self.valid():
            raise Exception('Invalid value for answer type %s: %s' % (self.answer_type, value))

    def valid(self):
        if not isinstance(self._hivemind_issue, HivemindIssue):
            raise Exception('No hivemind question set on option yet! Must set the hivemind question first before setting the value!')

        if self.answer_type != self._hivemind_issue.answer_type:
            LOG.error('Option value is not the correct answer type, got %s but should be %s' % (self.answer_type, self._hivemind_issue.answer_type))
            return False

        if self._hivemind_issue.constraints is not None and 'choices' in self._hivemind_issue.constraints:
            if self.value not in self._hivemind_issue.constraints['choices']:
                LOG.error('Option %s is not valid because this it is not in the allowed choices of this hiveminds constraints!' % self.value)
                raise Exception('Option %s is not valid because this it is not in the allowed choices of this hiveminds constraints!' % self.value)

        if self.answer_type == 'String' and self.is_valid_string_option():
            return True
        elif self.answer_type == 'Bool' and self.is_valid_bool_option():
            return True
        elif self.answer_type == 'Integer' and self.is_valid_integer_option():
            return True
        elif self.answer_type == 'Float' and self.is_valid_float_option():
            return True
        elif self.answer_type == 'Hivemind' and self.is_valid_hivemind_option():
            return True
        elif self.answer_type == 'Image' and isinstance(self.value, (str, unicode)):  # todo check for valid ipfs hash
            return True
        elif self.answer_type == 'Video' and isinstance(self.value, (str, unicode)):  # todo check for valid ipfs hash
            return True
        elif self.answer_type == 'Complex' and self.is_valid_complex_option():
            return True
        elif self.answer_type == 'Address' and self.is_valid_address_option():
            return True
        else:
            return False

    def is_valid_string_option(self):
        if not isinstance(self.value, (str, unicode)):
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_length' in self._hivemind_issue.constraints and len(self.value) < self._hivemind_issue.constraints['min_length']:
                return False
            elif 'max_length' in self._hivemind_issue.constraints and len(self.value) > self._hivemind_issue.constraints['max_length']:
                return False
            elif 'regex' in self._hivemind_issue.constraints and re.match(pattern=self._hivemind_issue.constraints['regex'], string=self.value) is None:
                return False

        return True

    def is_valid_float_option(self):
        if not isinstance(self.value, float):
            LOG.error('Option value %s is not a floating number value but instead is a %s' % (self.value, type(self.value)))
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                LOG.error('Option value is below minimum value: %s < %s' % (self.value, self._hivemind_issue.constraints['min_value']))
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                LOG.error('Option value is above maximum value: %s > %s' % (self.value, self._hivemind_issue.constraints['max_value']))
                return False
            elif 'decimals' in self._hivemind_issue.constraints and 0 < self._hivemind_issue.constraints['decimals'] != len(str(self.value)) - 1 - str(self.value).find('.'):
                LOG.error('Option value does not have the correct number of decimals (%s): %s' % (self._hivemind_issue.constraints['decimals'], self.value))
                return False

        return True

    def is_valid_integer_option(self):
        if not isinstance(self.value, (int, long)):
            LOG.error('Option value %s is not a integer value but instead is a %s' % (self.value, type(self.value)))
            return False

        if self._hivemind_issue.constraints is not None:
            if 'min_value' in self._hivemind_issue.constraints and self.value < self._hivemind_issue.constraints['min_value']:
                LOG.error('Option value is below minimum value: %s < %s' % (self.value, self._hivemind_issue.constraints['min_value']))
                return False
            elif 'max_value' in self._hivemind_issue.constraints and self.value > self._hivemind_issue.constraints['max_value']:
                LOG.error('Option value is above maximum value: %s > %s' % (self.value, self._hivemind_issue.constraints['max_value']))
                return False

        return True

    def is_valid_bool_option(self):
        if not isinstance(self.value, bool):
            LOG.error('Option value %s is not a boolean value but instead is a %s' % (self.value, type(self.value)))
            return False

        return True

    def is_valid_hivemind_option(self):
        try:
            isinstance(HivemindIssue(multihash=self.value), HivemindIssue)
        except Exception as ex:
            LOG.error('IPFS hash %s is not a valid hivemind: %s' % (self.value, ex))
            return False

        return True

    def is_valid_complex_option(self):
        if not isinstance(self.value, dict):
            return False

        if 'specs' in self._hivemind_issue.constraints:
            for spec_key in self._hivemind_issue.constraints['specs']:
                if spec_key not in self.value:
                    return False

            for spec_key in self.value.keys():
                if spec_key not in self._hivemind_issue.constraints['specs']:
                    return False

            for spec_key, spec_value in self.value.items():
                if self._hivemind_issue.constraints['specs'][spec_key] == 'String' and not isinstance(spec_value, (str, unicode)):
                    return False
                elif self._hivemind_issue.constraints['specs'][spec_key] == 'Integer' and not isinstance(spec_value, (int, long)):
                    return False
                elif self._hivemind_issue.constraints['specs'][spec_key] == 'Float' and not isinstance(spec_value, float):
                    return False

        return True

    def is_valid_address_option(self):
        if 'SIL' in self._hivemind_issue.constraints or 'LAL' in self._hivemind_issue.constraints:
            address = self._hivemind_issue.constraints['SIL']
            block_height = self._hivemind_issue.constraints['block_height'] if 'block_height' in self._hivemind_issue.constraints else 0

            if 'SIL' in self._hivemind_issue.constraints:
                data = get_sil(address=address, block_height=block_height)
                if 'SIL' not in data:
                    LOG.error('Unable to retrieve SIL of %s to verify constraints op hivemind option' % address)
                    return False

                for item in data['SIL']:
                    if item[0] == self.value:  # assume data in SIL is valid
                        return True

                return False

            elif 'LAL' in self._hivemind_issue.constraints:
                xpub = self._hivemind_issue.constraints['xpub']
                data = get_lal(address=address, xpub=xpub, block_height=block_height)
                if 'LAL' not in data:
                    LOG.error('Unable to retrieve LAL of %s to verify constraints of hivemind option' % address)
                    return False

                for item in data['LAL']:
                    if item[1] == self.value:  # assume data in LAL is valid
                        return True

                return False

        return valid_address(self.value) or valid_bech32_address(self.value)

    def info(self):
        """
        Get all details of the Option as a formatted string
        """
        ret = 'Option hash: %s' % self._multihash
        ret += '\nAnswer type: %s' % self.answer_type
        ret += '\nOption value: %s' % self.value

        return ret


class HivemindOpinion(IPFSDict):
    def __init__(self, multihash=None):
        """
        Constructor of the Opinion object

        :param multihash: The ipfs hash of the Opinion object (optional)
        """
        self.opinionator = None

        self.hivemind_issue_hash = None
        self._hivemind_issue = None  # must be private member so it doesn't get saved in the IPFSDict

        self.hivemind_state_hash = None
        self._hivemind_state = None # must be private member so it doesn't get saved in the IPFSDict

        self.ranked_choice = []
        self.auto_complete = None

        self.question_index = 0

        super(HivemindOpinion, self).__init__(multihash=multihash)

    def set(self, opinionator, ranked_choice):
        """
        Set the list of ranked option hashes

        :param opinionator: The id of the person expressing the opinion
        :param ranked_choice: A list of sorted option hashes
        """
        if not isinstance(self._hivemind_state, HivemindState):
            raise Exception('Hivemind state has not been set yet')

        self.opinionator = opinionator
        self.ranked_choice = ranked_choice

        if not self.valid():
            raise Exception('invalid ranked choice')

    def ranking(self):
        """
        Get the sorted list of option hashes

        :return: The list of sorted option ids
        """
        if self._hivemind_state.hivemind_issue().answer_type not in ['Integer', 'Float']:
            return self.ranked_choice
        elif self.auto_complete is None or len(self.ranked_choice) > 1:  # if more than one ranked choice is given, then auto_complete is overruled
            return self.ranked_choice
        elif self.auto_complete in ['MAX', 'MIN', 'CLOSEST', 'CLOSEST_HIGH', 'CLOSEST_LOW']:
            my_opinion_value = HivemindOption(multihash=self.ranked_choice[0]).value
            sorted_option_hashes = sorted(self._hivemind_state.options, key=lambda x: HivemindOption(multihash=x).value)

            if self.auto_complete == 'MAX':
                completed_ranking = [option_hash for option_hash in sorted_option_hashes if HivemindOption(
                    multihash=option_hash).value <= my_opinion_value]

            elif self.auto_complete == 'MIN':
                completed_ranking = [option_hash for option_hash in sorted_option_hashes if HivemindOption(
                    multihash=option_hash).value >= my_opinion_value]

            elif self.auto_complete == 'CLOSEST':
                completed_ranking = sorted(self._hivemind_state.options, key=lambda x: abs(HivemindOption(
                    multihash=x).value - my_opinion_value))

            elif self.auto_complete == 'CLOSEST_HIGH':
                completed_ranking = sorted(self._hivemind_state.options, key=lambda x: (abs(HivemindOption(
                    multihash=x).value - my_opinion_value), -HivemindOption(multihash=x).value))

            elif self.auto_complete == 'CLOSEST_LOW':
                completed_ranking = sorted(self._hivemind_state.options, key=lambda x: (abs(HivemindOption(
                    multihash=x).value - my_opinion_value), HivemindOption(multihash=x).value))

            else:
                raise Exception('Unknown auto_complete type: %s' % self.auto_complete)

            return completed_ranking

    def set_hivemind_state(self, hivemind_state_hash):
        self.hivemind_state_hash = hivemind_state_hash
        self._hivemind_state = HivemindState(multihash=self.hivemind_state_hash)

    def set_question_index(self, question_index):
        self.question_index = question_index

    def get_unranked_option_ids(self):
        """
        Get the list of option ids that have not been ranked yet

        :return: A list of option ids that have not been ranked yet
        """
        unranked = []
        for option_id in self._hivemind_issue.options:
            if option_id not in self.ranked_choice:
                unranked.append(option_id)

        return sorted(unranked)

    def info(self):
        """
        Get the details of this Opinion object in string format

        :return: the details of this Opinion object in string format
        """
        ret = '%s: ' % self.opinionator
        for i, option_hash in enumerate(self.ranked_choice):
            option = HivemindOption(multihash=option_hash)
            ret += '\n%s: %s' % (i+1, option.value)

        return ret

    def is_complete(self, ranked_choice=None):
        """
        Is this Opinion complete? Meaning are all option hashes present in the ranked_choice?

        :param ranked_choice: An optional list of option hashes
        :return: True or False
        """
        if ranked_choice is None:
            ranked_choice = self.ranked_choice

        return all(option_id in ranked_choice for option_id in self._hivemind_issue.options)

    def valid(self):
        """
        Is the Opinion object a valid opinion? Meaning are all option hashes in the ranked_choice valid?

        :return: True or False
        """
        if not isinstance(self._hivemind_state, HivemindState):
            return False

        if self.contains_duplicates() is True:
            return False

        return not any(option_hash not in self._hivemind_state.options for option_hash in self.ranked_choice)

    def contains_duplicates(self):
        """
        Does the Opinion object have duplicate option hashes in ranked_choice?

        :return: True or False
        """
        return len([x for x in self.ranked_choice if self.ranked_choice.count(x) >= 2]) > 0

    def load(self, multihash):
        super(HivemindOpinion, self).load(multihash=multihash)
        self.set_hivemind_state(hivemind_state_hash=self.hivemind_state_hash)


class HivemindState(IPFSDictChain):
    def __init__(self, multihash=None):
        self.hivemind_issue_hash = None
        self._hivemind_issue = None
        self.options = []
        self.opinions = [{}]  # opinions are recorded for each question separately
        self.weights = {}
        self.results = [{}]  # results are recorded for each question separately
        self.contributions = [{}]  # contributions are recorded for each question separately
        self.supporters = []
        self.selected = []  # A list of options that have been selected by the hivemind
        self.final = False  # if set to True, no more options or opinions can be added

        super(HivemindState, self).__init__(multihash=multihash)

    def hivemind_issue(self):
        return self._hivemind_issue

    def set_hivemind_issue(self, issue_hash):
        self.hivemind_issue_hash = issue_hash
        self._hivemind_issue = HivemindIssue(multihash=self.hivemind_issue_hash)
        self.opinions = [{} for _ in range(len(self._hivemind_issue.questions))]
        self.results = [{} for _ in range(len(self._hivemind_issue.questions))]
        self.contributions = [{} for _ in range(len(self._hivemind_issue.questions))]

    def load(self, multihash):
        super(HivemindState, self).load(multihash=multihash)
        self._hivemind_issue = HivemindIssue(multihash=self.hivemind_issue_hash)

    def clear_results(self, question_index=0):
        """
        Clear results of the hivemind
        """
        for opinionator in self.results[question_index]:
            self.results[question_index][opinionator] = {'win': 0, 'loss': 0, 'unknown': 0, 'score': 0}

    def add_option(self, option_hash, address=None, signature=None):
        """
        Add an option to the hivemind state

        If the hivemind issue has restrictions on addresses, then the address and signature are required
        If an address and signature is given, then it is also added to the list of supporters

        :param option_hash: The IPFS multihash of the option
        :param address: The address that supports the option (optional)
        :param signature: The signature of the message: 'IPFS=<option_hash>' by the address (optional)
        """
        if self.final is True:
            return

        if not isinstance(self._hivemind_issue, HivemindIssue):
            return

        if address is not None and signature is not None:
            if not verify_message(message='IPFS=%s' % option_hash, address=address, signature=signature):
                raise Exception('Can not add option: Signature is not valid')

        if self._hivemind_issue.restrictions is not None and 'addresses' in self._hivemind_issue.restrictions:
            if address not in self._hivemind_issue.restrictions['addresses']:
                raise Exception('Can not add option: there are address restrictions on this hivemind issue and address %s is not allowed to add options' % address)
            elif address is None or signature is None:
                    raise Exception('Can not add option: no address or signature given')

        if self._hivemind_issue.restrictions is not None and 'options_per_address' in self._hivemind_issue.restrictions:
            n_options = 0
            for supported_option_hash, supporter, _ in self.supporters:
                if supporter == address:
                    n_options += 1

            if n_options >= self._hivemind_issue.restrictions['options_per_address']:
                raise Exception('Can not add option: address %s already added too many options: %s' % (address, n_options))

        option = HivemindOption(multihash=option_hash)
        if isinstance(option, HivemindOption) and option.valid():
            if option_hash not in self.options:
                self.options.append(option_hash)
                for i in range(len(self._hivemind_issue.questions)):
                    self.results[i][option_hash] = {'win': 0, 'loss': 0, 'unknown': 0, 'score': 0}

                # If restrictions apply, then the address that adds the option is automatically also a supporter
                if address is not None and signature is not None:
                    self.support_option(option_hash=option_hash, address=address, signature=signature)

    def support_option(self, option_hash, address, signature):
        """
        Add support for an option

        :param option_hash: The IPFS multihash of the option
        :param address: The address that supports the option
        :param signature: the signature of the message 'IPFS=<option_hash>' by the address
        """
        if self.final is True:
            return

        if not verify_message(message='IPFS=%s' % option_hash, address=address, signature=signature):
            raise Exception('Can not support option: Signature is not valid')

        if option_hash not in self.options:
            raise Exception('Can not support option: %s not found' % option_hash)

        for supported_option_hash, supporter, _ in self.supporters:
            if supported_option_hash == option_hash and supporter == address:
                # address already supports this option
                return

        self.supporters.append((option_hash, address, signature))

    def add_opinion(self, opinion_hash, signature, weight=1.0, question_index=0):
        if self.final is True:
            return

        opinion = HivemindOpinion(multihash=opinion_hash)
        if not verify_message(address=opinion.opinionator, message='IPFS=%s' % opinion_hash, signature=signature):
            raise Exception('Can not add opinion: signature is invalid')

        if isinstance(opinion, HivemindOpinion) and opinion.valid():
            self.opinions[question_index][opinion.opinionator] = [opinion_hash, signature, int(time.time())]
            self.set_weight(opinionator=opinion.opinionator, weight=weight)

    def get_opinion(self, opinionator, question_index=0):
        """
        Get the Opinion object of a certain opinionator

        :param opinionator: The opinionator
        :param question_index: The index of the question in the HivemindQuestion (default=0)
        :return: An Opinion object
        """
        opinion = None
        if opinionator in self.opinions[question_index]:
            opinion = HivemindOpinion(multihash=self.opinions[question_index][opinionator])

        return opinion

    def set_weight(self, opinionator, weight=1.0):
        """
        Set the weight of a Opinion

        :param opinionator: The opinionator
        :param weight: The weight of the Opinion (default=1.0)
        """
        self.weights[opinionator] = weight

    def get_weight(self, opinionator):
        """
        Get the weight of an Opinion

        :param opinionator: The opinionator
        :return: The weight of the Opinion (type float)
        """
        return self.weights[opinionator]

    def info(self):
        """
        Print the details of the hivemind
        """
        ret = "================================================================================="
        ret += '\nHivemind id: ' + self._hivemind_issue.hivemind_id
        ret += '\nHivemind main question: ' + self._hivemind_issue.questions[0]
        ret += '\nHivemind description: ' + self._hivemind_issue.description
        if self._hivemind_issue.tags is not None:
            ret += '\nHivemind tags: ' + self._hivemind_issue.tags
        ret += '\nAnswer type: ' + self._hivemind_issue.answer_type
        if self._hivemind_issue.constraints is not None:
            ret += '\nOption constraints: ' + str(self._hivemind_issue.constraints)
        ret += '\n' + "================================================================================="
        ret += '\n' + self.options_info()

        for i, question in enumerate(self._hivemind_issue.questions):
            ret += '\nHivemind question %s: %s' % (i, self._hivemind_issue.questions[i])
            ret += '\n' + self.opinions_info(question_index=i)
            ret += '\n' + self.results_info(question_index=i)

        return ret

    def options_info(self):
        """
        Get detailed information about the options as a formatted string

        :return: A string containing all information about the options
        """
        ret = "Options"
        ret += "\n======="
        for i, option_hash in enumerate(self.options):
            ret += '\nOption %s:' % (i + 1)
            option = HivemindOption(multihash=option_hash)
            ret += '\n' + option.info()
            ret += '\n'

        return ret

    def opinions_info(self, question_index=0):
        """
        Print out a list of the Opinions of the hivemind
        """
        ret = "Opinions"
        ret += "\n========"
        # opinion_data is a list containing [opinion_hash, signature of 'IPFS=opinion_hash', timestamp]
        for opinionator, opinion_data in self.opinions[question_index].items():
            ret += '\nTimestamp: %s, Signature: %s' % (opinion_data[2], opinion_data[1])
            opinion = HivemindOpinion(multihash=opinion_data[0])
            ret += '\n' + opinion.info()
            ret += '\n'

        return ret

    def calculate_results(self, question_index=0):
        """
        Calculate the results of the hivemind
        """
        LOG.info('Calculating results for question %s...' % question_index)
        self.clear_results(question_index=question_index)

        # if selection mode is 'Exclude', we must exclude previously selected options from the results
        if self._hivemind_issue.on_selection == 'Exclude':
            selected_options = [selection[question_index] for selection in self.selected]
            available_options = [option_hash for option_hash in self.options if option_hash not in selected_options]
        else:
            available_options = self.options

        for a, b in combinations(available_options, 2):
            for opinionator in self.opinions[question_index]:
                winner = compare(a, b, self.opinions[question_index][opinionator][0])
                weight = self.weights[opinionator] if opinionator in self.weights else 0.0
                if winner == a:
                    self.results[question_index][a]['win'] += weight
                    self.results[question_index][b]['loss'] += weight
                elif winner == b:
                    self.results[question_index][b]['win'] += weight
                    self.results[question_index][a]['loss'] += weight
                elif winner is None:
                    self.results[question_index][a]['unknown'] += weight
                    self.results[question_index][b]['unknown'] += weight

        self.calculate_scores(question_index=question_index)
        self.calculate_contributions(question_index=question_index)
        results_info = self.results_info(question_index=question_index)
        for line in results_info.split('\n'):
            LOG.info(line)

    def calculate_scores(self, question_index=0):
        """
        Calculate the scores of all Options
        """
        for option_id in self.results[question_index]:
            if self.results[question_index][option_id]['win'] + self.results[question_index][option_id]['loss'] + self.results[question_index][option_id]['unknown'] > 0:
                self.results[question_index][option_id]['score'] = self.results[question_index][option_id]['win'] / float(
                    self.results[question_index][option_id]['win'] + self.results[question_index][option_id]['loss'] + self.results[question_index][option_id]['unknown'])

    def get_score(self, option_hash, question_index=0):
        return self.results[question_index][option_hash]['score']

    def get_options(self, question_index=0):
        """
        Get the list of Options as sorted by the hivemind

        :return: A list of Option objects sorted by highest score
        """
        return [HivemindOption(multihash=option[0]) for option in sorted(self.results[question_index].items(), key=lambda x: x[1]['score'], reverse=True)]

    def consensus(self, question_index=0):
        sorted_options = self.get_options(question_index=question_index)
        if len(sorted_options) == 0:
            return None
        elif len(sorted_options) == 1:
            return sorted_options[0].value
        # Make sure the consensus is not tied between the first two options
        elif len(sorted_options) >= 2 and self.get_score(option_hash=sorted_options[0].multihash()) > self.get_score(option_hash=sorted_options[1].multihash()):
            return sorted_options[0].value
        else:
            return None

    def ranked_consensus(self, question_index=0):
        return [option.value for option in self.get_options(question_index=question_index)]

    def get_consensus(self, question_index=0):
        if self._hivemind_issue.consensus_type == 'Single':
            return self.consensus(question_index=question_index)
        elif self._hivemind_issue.consensus_type == 'Ranked':
            return self.ranked_consensus(question_index=question_index)

    def results_info(self, question_index=0):
        """
        Print out the results of the hivemind
        """
        ret = self._hivemind_issue.questions[question_index]
        ret += '\nResults:\n========'
        i = 0
        for option_hash, option_result in sorted(self.results[question_index].items(), key=lambda x: x[1]['score'], reverse=True):
            i += 1
            option = HivemindOption(multihash=option_hash)
            ret += '\n%s: (%g%%) : %s' % (i, round(option_result['score']*100, 2), option.value)

        ret += '\n================'
        ret += '\nCurrent consensus: %s' % self.get_consensus(question_index=question_index)
        ret += '\n================'

        ret += '\nContributions:'
        ret += '\n================'
        for opinionator, contribution in self.contributions[question_index].items():
            ret += '\n%s: %s' % (opinionator, contribution)
        ret += '\n================'

        return ret

    def calculate_contributions(self, question_index):
        # Clear contributions
        self.contributions[question_index] = {}

        deviances = {}
        total_deviance = 0
        multipliers = {}

        # sort the option hashes by highest score
        option_hashes_by_score = [option[0] for option in sorted(self.results[question_index].items(), key=lambda x: x[1]['score'], reverse=True)]

        # sort the opinionators by the timestamp of their opinion
        opinionators_by_timestamp = [opinionator for opinionator, opinion_data in sorted(self.opinions[question_index].items(), key=lambda x: x[1][2])]

        # exclude the opinionators with weight 0
        opinionators_by_timestamp = [opinionator for opinionator in opinionators_by_timestamp if self.weights[opinionator] > 0.0]

        for i, opinionator in enumerate(opinionators_by_timestamp):
            deviance = 0
            opinion = HivemindOpinion(multihash=self.opinions[question_index][opinionator][0])

            # Calculate the 'early bird' multiplier (whoever gives their opinion first gets the highest multiplier, value is between 0 and 1), if opinion is an empty list, then multiplier is 0
            multipliers[opinionator] = 1 - (i/float(len(opinionators_by_timestamp))) if len(opinion.ranked_choice) > 0 else 0

            # Calculate the deviance of the opinion, the closer the opinion is to the final result, the lower the deviance
            for j, option_hash in enumerate(option_hashes_by_score):
                if option_hash in opinion.ranked_choice:
                    deviance += abs(j - opinion.ranked_choice.index(option_hash))
                else:
                    deviance += len(option_hashes_by_score)-j

            total_deviance += deviance
            deviances[opinionator] = deviance

        if total_deviance != 0:  # to avoid divide by zero
            self.contributions[question_index] = {opinionator: (1-(deviances[opinionator]/float(total_deviance)))*multipliers[opinionator] for opinionator in deviances}
        else:  # everyone has perfect opinion, but contributions should still be multiplied by the 'early bird' multiplier
            self.contributions[question_index] = {opinionator: 1*multipliers[opinionator] for opinionator in deviances}

    def select_consensus(self):
        # Selecting an option only makes sense if the consensus type is 'Single'
        """
        Mark the current consensus as being 'selected'

        :return: a list containing the option with highest consensus for each question
        """
        if self._hivemind_issue.consensus_type != 'Single':
            return

        # Get the option with highest consensus for each question
        selection = [self.get_consensus(question_index=question_index) for question_index in range(len(self._hivemind_issue.questions))]
        self.selected.append(selection)

        if self._hivemind_issue.on_selection is None:
            return
        elif self._hivemind_issue.on_selection == 'Finalize':
            # The hivemind is final, no more options or opinions can be added
            self.final = True
        elif self._hivemind_issue.on_selection == 'Exclude':
            # The selected option is excluded from future results
            pass
        elif self._hivemind_issue.on_selection == 'Reset':
            # All opinions are reset
            self.opinions = [{}]
        else:
            raise NotImplementedError('Unknown selection mode: %s' % self._hivemind_issue.on_selection)

        self.save()
        return selection


def compare(a, b, opinion_hash):
    """
    Helper function to compare 2 Option objects against each other based on a given Opinion

    :param a: The first Option object
    :param b: The second Option object
    :param opinion_hash: The Opinion object
    :return: The Option that is considered better by the Opinion
    If one of the Options is not given in the Opinion object, the other option wins by default
    If both Options are not in the Opinion object, None is returned
    """
    opinion = HivemindOpinion(multihash=opinion_hash)
    ranked_choice = opinion.ranked_choice
    if a in ranked_choice and b in ranked_choice:
        if ranked_choice.index(a) < ranked_choice.index(b):
            return a
        elif ranked_choice.index(a) > ranked_choice.index(b):
            return b
    elif a in ranked_choice:
        return a
    elif b in ranked_choice:
        return b
    else:
        return None
