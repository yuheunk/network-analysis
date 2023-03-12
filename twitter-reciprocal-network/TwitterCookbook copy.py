#!/usr/bin/env python
# coding: utf-8

import twitter
import sys
from functools import partial
from sys import maxsize as maxint
from urllib.parse import unquote
from urllib.error import URLError
from http.client import BadStatusLine
import time

## TWITTER COOKBOOK CODE
def oauth_login():
    # XXX: Go to http://twitter.com/apps/new to create an app and get values
    # for these credentials that you'll need to provide in place of these
    # empty string values that are defined as placeholders.
    # See https://developer.twitter.com/en/docs/basics/authentication/overview/oauth
    # for more information on Twitter's OAuth implementation.
    
    CONSUMER_KEY = ''
    CONSUMER_SECRET = ''
    OAUTH_TOKEN = ''
    OAUTH_TOKEN_SECRET = ''
    
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                               CONSUMER_KEY, CONSUMER_SECRET)
    
    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api

def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 
    
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
    
        if wait_period > 3600: # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e
    
        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes
    
        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429: 
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'                  .format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise

def get_user_profile(twitter_api, screen_names=None, user_ids=None):
   
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None),     "Must have screen_names or user_ids, but not both"
    
    items_to_info = {}

    items = screen_names or user_ids
    
    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.
        
        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup, 
                                            screen_name=items_str)
        else: # user_ids
            response = make_twitter_request(twitter_api.users.lookup, 
                                            user_id=items_str)
    
        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else: # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info

def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None),     "Must have screen_name or user_id, but not both"
    
    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters
    
    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, 
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, 
                                count=5000)

    friends_ids, followers_ids = [], []
    
    for twitter_api_func, limit, ids, label in [
                    [get_friends_ids, friends_limit, friends_ids, "friends"], 
                    [get_followers_ids, followers_limit, followers_ids, "followers"]
                ]:
        
        if limit == 0: continue
        
        cursor = -1
        while cursor != 0:
        
            # Use make_twitter_request via the partially bound callable...
            if screen_name: 
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else: # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']
        
            print('Fetched {0} total {1} ids for {2}'.format(len(ids),                  label, (user_id or screen_name)),file=sys.stderr)
        
            # XXX: You may want to store data during each iteration to provide an 
            # an additional layer of protection from exceptional circumstances
        
            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]


### My Code ###
def get_reciprocal_ids(twitter_api, user_id=None, screen_name=None, limit=500):
    """
    Get the seed id(int) and reciprocal friend ids(list of int)
    """
    if screen_name:  # If screen name is provided
        seed_id = str(twitter_api.users.show(screen_name=screen_name)['id'])
        print(f'---Got {screen_name} id')
    elif user_id:  # If user id is provided
        seed_id = user_id
    
    # Get the friends and followers id list
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api, user_id=seed_id, 
                                                           friends_limit=limit, followers_limit=limit)
    reciprocal_friend_ids = list(set(friends_ids) & set(followers_ids))  # Get the reciprocal friend id list
    print(f'---Got reciprocal friends ids')
    return seed_id, reciprocal_friend_ids


def most_followers(twitter_api, user_lst, k=5):
    """
    Get user ids with the most followers (top k)
    """
    # Get the profile information for each user in the user id list
    profile_lst = get_user_profile(twitter_api, user_ids=user_lst)
    # Next extract the user id and a followers_count number
    follower_cnt_lst = [(k, profile_lst[k]['followers_count']) for k in profile_lst.keys()]
    # Sort the list of tuples by the followers_count number and get the top k
    top_followers_lst = sorted(follower_cnt_lst, key=lambda x: x[1], reverse=True)[:k]
    # Extract the ids (first tuple)
    top_followers_id = [id for (id, _) in top_followers_lst]
    
    print(f'---Got top {k} followers')
    return top_followers_id


def crawl_network(twitter_api, screen_name, limit=500):
    """
    Crawler code for creating a network.
    - screen_name: seed user name to start the network
    - limit: Limits the number of friend and follower list

    -- Data save format (json)
    result = {'seed id': [id1, id2, id3, .., id5],
              'id1': [id1-1, id1-2, ..., id1-5],
              'id2': [id2-1, id2-2, ..., id2-5],
              ...}
    """
    # Initialize variables
    network = {}  # Crawled network
    num_nodes = []  # Number of nodes

    # Get the id and list of reciprocal friends from the seed user
    seed_id, reciprocal_friend_ids = get_reciprocal_ids(twitter_api, screen_name=screen_name, limit=limit)
    # Retrieve 5 reciprocal friend ids with the most followers (top 5)
    top_followers = most_followers(twitter_api, reciprocal_friend_ids, 5)
    network[seed_id] = top_followers  # Add to network
    
    # This counts the number of node collected for the network
    num_nodes.append(seed_id)
    num_nodes += top_followers
    num_ids = len(set(num_nodes))
    
    # Run until number of node reaches at least 100
    while num_ids < 100:
        print('start!')
        tmp_lst = []  # Initialize temporary list
        
        for user_id in top_followers:
            # For all top_followers list repeat the step done with the seed user
            id, reciprocal_friend_ids = get_reciprocal_ids(twitter_api, user_id=user_id, limit=limit)
            top_followers = most_followers(twitter_api, reciprocal_friend_ids, 5)
            network[id] = top_followers  # Add to network
            
            num_nodes.append(id)
            num_nodes+=top_followers
            # Update the temporary list with all top 5 reciprocal friends from top_followers list
            tmp_lst += top_followers
        
        # If the num_ids is less than 100, we will repeat the crawling process
        # Update num_ids
        num_ids = len(set(num_nodes))
        print(f"---Crawled {num_ids} nodes.")

        top_followers = tmp_lst  # Update the top_followers list to temporary list
    
    return network