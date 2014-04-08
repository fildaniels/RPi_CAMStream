import cv2.cv as cv
from tornado.websocket import WebSocketHandler
import tornado.web
import tornado.httpserver
from tornado.ioloop import IOLoop
import time


WIDTH = 480
HEIGHT = 360
FPS = 30
class HttpHandler(tornado.web.RequestHandler):
    def initialize(self):
            pass

    def get(self):
        with open("./index.html") as f:
            for line in f.readlines():
                self.write(line)
            self.finish()

class WSHandler(WebSocketHandler):
    def initialize(self, camera):
        self.camera = camera
        self.state = True

    def open(self):
        print("connection opened")

        if isinstance(self.camera, Camera):
            while self.state:
                cv.WaitKey(1000/FPS)
                self.loop()
        else:
            for foo in self.camera.capture_continuous(self.camera.stream, "jpeg", use_video_port=True):
                self.camera.stream.seek(0)
                self.write_message(self.camera.stream.read(), binary=True)
                self.camera.stream.seek(0)
                self.camera.stream.truncate()

    def loop(self):
        img = self.camera.takeImage()
        self.write_message(img, binary=True)

    def on_message(self, message):
        print message
        if str(message) == "close":
            self.on_close()

    def on_close(self):
        self.state = False
        IOLoop.instance().stop()

class Camera():
    def __init__(self):
        self.capture = cv.CaptureFromCAM(0)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, WIDTH)
        cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, HEIGHT)
    
    def takeImage(self):
        img = cv.QueryFrame(self.capture)
        img = cv.EncodeImage(".jpg", img).tostring()
        return img

def piCamera():
    import picamera, io
    camera = picamera.PiCamera()
    camera.resolution = (WIDTH, HEIGHT)
    camera.framerate = FPS
    camera.led = False
    camera.stream = io.BytesIO()
    time.sleep(2)
    return camera

def main():
    try:
        camera = piCamera()
    except:
        camera = Camera()
    print "complete initialization"
    app = tornado.web.Application([
        (r"/", HttpHandler),
        (r"/camera", WSHandler, dict(camera=camera)),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8080)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
