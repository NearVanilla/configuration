#!/usr/bin/env python3
# vim: sw=2

import pickle
import sys
import os
import email
import quopri
import base64
import time
import requests
import itertools
import re
from pprint import pprint
from html2text import html2text
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def error(*args, **kwargs):
  print(*args, **kwargs, file=sys.stderr)
  sys.exit(1)

def chunkify(l, n):
  for i in range(0, len(l), n):
    yield itertools.islice(l, i, i+n)

def execute_webhook(url, payload):
  try:
    r = requests.post(url, json=payload)
    r.raise_for_status()
  except:
    pprint(payload, stream=sys.stderr)
    print(r.json(), file=sys.stderr)
    raise


def notify(url, messages, extra_data={}, delay=1):
  max_size = 1000
  oversize_mark = '\n**<--- SNIP --->**'
  for chunk in chunkify(messages, 3):
    data = {
      'embeds': [
        {
          'title': msg['subject'],
          'description': msg['body'] if len(msg['body']) <= max_size else msg['body'][:(max_size-len(oversize_mark))] + oversize_mark,
        } for msg in chunk
      ]
    }
    data.update(extra_data)

    execute_webhook(url, data)
    if delay:
      time.sleep(delay)

def _get_emails_with_labels(service, label_ids=[], user_id='me'):
  """List all Messages of the user's mailbox with label_ids applied.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

  Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
  """
  response = service.users().messages().list(userId=user_id,
                                             labelIds=label_ids).execute()
  messages = []
  if 'messages' in response:
    messages.extend(response['messages'])

  while 'nextPageToken' in response:
    page_token = response['nextPageToken']
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids,
                                               pageToken=page_token).execute()
    messages.extend(response['messages'])

  return messages

def get_label_by_name(service, label, user_id='me'):
  results = service.users().labels().list(userId=user_id).execute()
  labels = results.get('labels', [])

  if not labels:
    error('No labels found.')
  else:
    lab = [l for l in labels if l['name'] == label]
    if not lab:
      error(f'Label ${label} not found. Labels: ${[l["name"] for l in labels]}')
    return lab[0]


def get_emails(service, label, user_id='me'):
  lab = get_label_by_name(service, label)
  return _get_emails_with_labels(service, label_ids=[lab['id']], user_id=user_id)

def get_email(service, msg_id, user_id='me'):
  message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
  #print(message['raw'].encode('ASCII'))
  msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
  mime_msg = email.message_from_bytes(msg_str)
  return {
    'body': get_email_body(mime_msg),
    'subject': str(email.header.make_header(email.header.decode_header(mime_msg['Subject']))),
    'snippet': message['snippet'],
  }

def cleanup_body(mails):
  deliner = re.compile(r'\n\s*\n')
  for mail in mails:
    body = mail['body'].replace(b'    ', b'<br/>') # Gmail forms and such don't send newlines
    unmimed = quopri.decodestring(body)
    markdown = html2text(unmimed.decode(errors='ignore')) # TODO: FIX
    cmark = deliner.sub('\n\n', markdown)
    mail['body'] = cmark
  return mails

def get_email_body(mail):
  # https://stackoverflow.com/a/32840516
  if mail.is_multipart():
    for part in mail.walk():
      ctype = part.get_content_type()
      cdispo = str(part.get('Content-Disposition'))
      # skip any text/plain (txt) attachments
      if ctype == 'text/plain' and 'attachment' not in cdispo:
        return part.get_payload(decode=True)
  # not multipart - i.e. plain text, no attachments, keeping fingers crossed
  else:
    return mail.get_payload(decode=True)

def load_credentials(credf, tokenf):
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists(tokenf):
    with open(tokenf, 'rb') as token:
      creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(credf, SCOPES)
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(tokenf, 'wb') as token:
      pickle.dump(creds, token)
  return creds


def mark_emails_processed(service, emails, new_label, old_label, user_id='me'):
  new_label_id = get_label_by_name(service, new_label)['id']
  old_label_id = get_label_by_name(service, old_label)['id']
  msg_labels = {
    'removeLabelIds': [ new_label_id ],
    'addLabelIds': [ old_label_id ],
  }
  for msg in emails:
    service.users().messages().modify(userId=user_id, id=msg['id'],
                                      body=msg_labels).execute()

def main():
  credentials_file = 'credentials.json'
  token_file = 'token.pickle'
  new_label = os.environ['NEW_LABEL']
  old_label = os.environ['OLD_LABEL']
  url = os.environ['URL']
  error_msg = os.environ.get('ERROR_MSG')
  data = {
    'username': os.environ['USERNAME'],
    'avatar_url': os.environ['AVATAR_URL'],
  }

  emails = None
  try:
    creds = load_credentials(credentials_file, token_file)
    service = build('gmail', 'v1', credentials=creds)
    emails = get_emails(service, new_label)
    messages = [ get_email(service, mail['id']) for mail in emails ]
    notify(url, cleanup_body(messages), data)
  except Exception as e:
    print(f"{'#'*10} ERROR OCCURRED: {e} {'#'*10}" , file=sys.stderr)
    if error_msg:
      msg = {
        'content': error_msg,
      }
      msg.update(data)
      execute_webhook(url, msg)
    raise
  finally:
    if emails:
      mark_emails_processed(service, emails, new_label, old_label)

if __name__ == '__main__':
    main()
