import logging
import time
import configargparse
import praw
import yaml
import requests

logger = logging.getLogger('prap')

def setup(file=None):

    logger.setLevel(logging.DEBUG)
    if file is not None:
        handler = logging.FileHandler(file)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    logger.debug(time.asctime())


def parser():
    p = configargparse.ArgumentParser()
    p.add('--config', '-c', required=False, is_config_file=True, help='config file path')
    p.add('--username', '-u', type=str, required=True, env_var='REDDIT_USERNAME',
          help='username')
    p.add('--password', '-p', type=str, required=True, env_var='REDDIT_PASSWORD',
          help='password')
    p.add('--submission-config', '-S', type=str, default='config.yml', env_var='SUBMISSION_CONFIG',
          help='file from which to read reddit post and webhook config')
    p.add('--subreddit', '-s', type=str, default='reddit_bot_test', env_var='REDDIT_SUBREDDIT',
          help='subreddit on which to post')
    p.add('--webhook', '-w', type=str, required=False, default=None, env_var='DISCORD_WEBHOOK',
                   help='Discord webhook where to post message on success')
    p.add('--flair', '-f', type=str, required=False, default=None, env_var='SUBREDDIT_FLAIR',
                   help='Subreddit flair to assign to the submission')
    p.add('--remove-webhook', '-r', type=str, required=False, default=None, env_var='REMOVE_WEBHOOK',
                   help='Save the previous webhook to given file, and if present - remove it after posting new one')
    return p.parse_args()

def get_flair_by_text(subreddit, flair_name):
    for flair in subreddit.flair.link_templates:
        if flair['text'] == flair_name:
            return flair['id']
    raise ValueError(f"No such flair with name {flair_name}")

def submit_to_reddit(args, config):
    reddit = praw.Reddit(client_id='RITQTVDBJ_yfJw',
                         client_secret='5lhHsOfIns_V3FknXRerXzmxVhA',
                         password=args.password,
                         user_agent='AutoPoster by /u/WhoTookAllNicks',
                         username=args.username)
    logger.info(f'Logged in as {reddit.user.me()}')
    title = config['title']
    content = config['content']
    subreddit = reddit.subreddit(args.subreddit)
    if args.flair:
        flair_id = get_flair_by_text(subreddit, args.flair)
    else:
        flair_id = None
    submission = subreddit.submit(title=title, selftext=content, flair_id=flair_id)
    logger.info(f'Posted "{title}" at {submission.url} succesfully')
    return submission

def post_webhook(args, config, submission):
    data = config['webhook']
    data['content'] = data['content'].format(submission=submission)
    response = requests.post(f"{args.webhook}?wait=true", json=data)
    response.raise_for_status()
    logger.info('Posted webhook sucessfully')
    return response.json()

def remove_webhook(args, message_id):
    requests.delete(f"{args.webhook}/messages/{message_id}").raise_for_status()
    logger.info('Deleted previous webhook sucessfully')

def main(args):
    try:
        with open(args.submission_config) as f:
            config = yaml.load(f)
        submission = submit_to_reddit(args, config)
        if args.webhook:
            response = post_webhook(args, config, submission)
            if args.remove_webhook:
                current_msg_id = response["id"]
                with open(args.remove_webhook, 'a+') as f:
                    f.seek(0)
                    previous_id = f.readline().strip()
                    f.seek(0)
                    f.truncate(0)
                    f.write(current_msg_id)
                if previous_id:
                    remove_webhook(args, previous_id)
    except Exception as err:
        logger.exception("Failed to execute.")
        raise

if __name__ == '__main__':
    setup('PRAP.log')
    main(parser())
