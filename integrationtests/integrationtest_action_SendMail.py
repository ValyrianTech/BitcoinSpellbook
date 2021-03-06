#!/usr/bin/env python
# -*- coding: utf-8 -*-
from helpers.setupscripthelpers import spellbook_call, clean_up_actions


print('Starting Spellbook integration test: SendMail actions')
print('----------------------------------------------\n')

# Clean up actions if necessary
clean_up_actions(action_ids=['integrationtest_action_SendMail'])

#########################################################################################################
# SendMail actions
#########################################################################################################
action_name = 'integrationtest_action_SendMail'
mail_recipients = 'someone@example.com'
mail_subject = 'example email subject'
mail_body_template = 'template1'

# --------------------------------------------------------------------------------------------------------

print('Creating test action: SendMailAction')
response = spellbook_call('save_action', '-t=SendMail', action_name, '-mr=%s' % mail_recipients, '-ms=%s' % mail_subject, "-mb=%s" % mail_body_template)
assert response is None

# --------------------------------------------------------------------------------------------------------
print('Getting the list of configured action_ids')
response = spellbook_call('get_actions')
assert action_name in response

# --------------------------------------------------------------------------------------------------------
print('Getting the action config of the action we just created')
response = spellbook_call('get_action_config', action_name)
assert response['id'] == action_name
assert response['action_type'] == 'SendMail'
assert response['mail_recipients'] == mail_recipients
assert response['mail_subject'] == mail_subject
assert response['mail_body_template'] == mail_body_template

# --------------------------------------------------------------------------------------------------------
print('Running the action we just created')
response = spellbook_call('run_action', action_name)
assert response is 'true' if mail_recipients != 'someone@example.com' else 'false'  # example.com is a reserved domain, so will always fail
