import tornado.httpserver
import tornado.web
import tornado.auth

from bleach import Bleach

import os

import re

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
            self.twitter_request("/statuses/home_timeline",
                                 access_token=self.get_current_user()['access_token'],
                                 callback=self.async_callback(self._on_finish_post),
                                 since_id=since) 

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

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('user')
        self.redirect('/')

settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
    "twitter_consumer_key": 'hZ2SGymCyji0dLoieJeFbg',
    "twitter_consumer_secret": 'egGqGY7Ye9JzL8RyrxVt0OsqVvhuUD0tryaPN55TA8',
    "login_url": "/login",
    "xsrf_cookies": False,
    "auto_reload": True,
    "debug": True
} 

application = tornado.web.Application([
    (r"/login", TwitterAuthHandler),
    (r"/logout", LogoutHandler),
    (r"/", TwitterStreamHandler)
], **settings) 

def main():
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start() 
 
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt, e:
        pass 
