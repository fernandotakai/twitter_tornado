import tornado.httpserver
import tornado.web
import tornado.auth

from tornado.options import define, options

from bleach import Bleach

import os
import re
import logging

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class TwitterStreamHandler(BaseHandler,
                  tornado.auth.TwitterMixin):

        @tornado.web.authenticated
        @tornado.web.asynchronous 
        def get(self):
            self.twitter_request("/statuses/home_timeline",
                                 access_token=self.get_current_user()['access_token'],
                                 callback=self.async_callback(self._on_finish_get), count=50)

        @tornado.web.authenticated
        @tornado.web.asynchronous  
        def post(self):
            since = self.get_argument('since')
            logging.info(since)
            self.twitter_request("/statuses/home_timeline",
                                 access_token=self.get_current_user()['access_token'],
                                 callback=self.async_callback(self._on_finish_post),
                                 since_id=since, count=200) 

        def _on_finish_get(self, posts):
            if not posts:
                raise tornado.web.HTTPError(500);

            for post in posts:
                post['text'] = self._proccess_tweet(post['text'])

            self.finish(self.render_string("stream.html", posts=posts))

        def _on_finish_post(self, posts):
            if not posts:
                raise tornado.web.HTTPError(500);

            for post in posts:
                post['text'] = self._proccess_tweet(post['text'])
                post['html'] = self.render_string("post.html", post=post)

            self.finish(tornado.escape.json_encode(posts)) 

        def _proccess_tweet(self, text):
            if not getattr(self, 'bleach', None):
                self.bleach = Bleach()

            text = re.sub(r'(?m)(^|\s)@(\w+)', lambda m: m.group(1) + '<a href="http://twitter.com/' + m.group(2) + '"> @' + m.group(2) + '</a>', text) 
            text = self.bleach.linkify(text)

            return text

class TwitterAuthHandler(BaseHandler,
                  tornado.auth.TwitterMixin):

    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return

        self.authorize_redirect() 

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed") 
        else:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
            self.redirect("/")

class TwitterUpdaterHandler(BaseHandler, 
                    tornado.auth.TwitterMixin):

    @tornado.web.asynchronous
    @tornado.web.authenticated
    def post(self):
        status = self.get_argument('status')

        self.twitter_request("/statuses/update",
                            post_args={"status": status.encode("utf-8")},
                            access_token=self.get_current_user()['access_token'],
                            callback=self.async_callback(self._on_post))

    def _on_post(self, status):
        if not status:
            raise tornado.web.HTTPError(500)
        else:
            self.finish(tornado.web.escape.json_encode(status));

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "twitter_consumer_key": 'Zm03T6WTg3xX6wGN4YNmnQ',
    "twitter_consumer_secret": 'wa5juB4Av18uO9HyOzbL3RuG99gg1UZVPaoGa7Xlw',
    "login_url": "/login",
    "xsrf_cookies": False,
    "auto_reload": True,
    "debug": True
} 

application = tornado.web.Application([
    (r"/login", TwitterAuthHandler),
    (r"/logout", LogoutHandler),
    (r"/post", TwitterUpdaterHandler),
    (r"/", TwitterStreamHandler)
], **settings) 

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start() 
 
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt, e:
        pass 
