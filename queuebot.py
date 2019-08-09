try:
    import http.server
    from twitchio.ext import commands
    import json
    from re import search,findall,IGNORECASE,MULTILINE 
    from sys import argv
    import sys
    import os
    import threading
    import time
    import requests
    import ctypes
    import steam
    import socketserver
    import subprocess
    import tkinter
except ImportError as e:
    print(e)

class Window(tkinter.Frame):

    def __init__(self,master=None):
        tkinter.Frame.__init__(self, master)
        self.master=master
        self.level = tkinter.StringVar(self, value='No levels in queue')
        self.twitch = tkinter.StringVar(self, value='No levels in queue')
        self.author = tkinter.StringVar(self, value='No levels in queue')
        self.link = tkinter.StringVar(self, value='No levels in queue')
        self.count = False
        self.update_texts()
        self.init_window()

    def init_window(self):
        self.master.title("Portal World")
        self.pack(fill=tkinter.BOTH, expand=1)
        tkinter.Label(self, text='Level name:').pack()
        tkinter.Label(self, textvariable=self.level, wraplength=390).pack()
        tkinter.Label(self, text='Level creator:').pack()
        tkinter.Label(self, textvariable=self.author, wraplength=390).pack()
        tkinter.Label(self, text='Level submitter:').pack()
        tkinter.Label(self, textvariable=self.twitch, wraplength=390).pack()
        tkinter.Label(self, text='Level link:').pack()
        tkinter.Label(self, textvariable=self.link, wraplength=390).pack()
        tkinter.Button(self,text='Copy link',command=self.get_link).pack()
        tkinter.Button(self,text='Next level',command=self.next).pack()
        tkinter.Button(self,text='Quit',command=self.stop).pack()

    def update_texts(self):
        with open(path,'r') as infile:
            level = json.load(infile)
        if len(level) == 0:
            self.level.set('No levels in queue')
            self.twitch.set('No levels in queue')
            self.author.set('No levels in queue')
            self.link.set('No levels in queue')
        else:
            self.level.set(level[0]['level'])
            self.twitch.set(level[0]['twitch'])
            self.author.set(level[0]['nick'])
            self.link.set(level[0]['link'])
        self.list = level
        
    def get_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.link.get())
        self.update()
    
    def next(self):
        if (len(self.list) != 0 and str(self.list[0]['level']) == str(self.level.get()) and self.count) or len(self.list) == 1:
            self.list.pop(0)
            self.count = False
            with open(path,'w') as outfile:
                json.dump(self.list,outfile)
            self.update_texts()
        else:
            self.update_texts()
            self.count = True

    def stop(self):
        self.master.destroy()


class Bot(commands.Bot):

    def __init__(self):
        with open(path3 + '/def.txt','r') as infile:
            default = infile.read()
        with open(path3 + '/settings.txt', 'r') as infile:
            settings = infile.read()
            mat = findall(r'"(.+?)"', settings)
            if len(mat) != 4 or default == settings:
                print('Error, please fill settings.txt completely in first.')
                exit()
        self.move = False
        self.user_count = mat[3]
        super().__init__(irc_token=mat[0],prefix='!', nick=mat[1], initial_channels=[mat[2]])
    
    def close(self):
        os.system('exit')

    # Events don't need decorators when subclassed
    async def event_ready(self):
        print(f'Ready | {self.nick}')

    async def event_message(self, message):
        await self.handle_commands(message)

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            return
        raise error

    # Commands use a different decorator
    @commands.command(name='add',aliases=['submit'])
    async def add(self, ctx):
        mat = findall(r"""(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])""", ctx.content,IGNORECASE)
        if mat:
            with open(path,'r') as infile:
                data = json.load(infile)
            
            levelLink = mat[0]
            while True:
                try:
                    req = requests.get(levelLink)
                except Exception:
                    pass
                else:
                    break
            if req.ok:
                site = str(req.content)
                mat = findall(r"""<div class="[^"]*?workshopItemTitle[^"]*?">(.*?)<\/div>|<div class="[^"]*?workshopItemTitle[^"]*?">(.*?)<\/div>|<a class="friendBlockLinkOverlay" href="(.*?)">""",site,IGNORECASE | MULTILINE)
                if mat:
                    levelName = mat[0][0]
                    authorLink = mat[1][2]
    
                    aid = steam.steamid.from_url(authorLink)
                    request = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=ABCE07D6D3E64ECBB4733E9E3DA30892&steamids=' + str(aid.as_64)

                    uinfo = steam.webapi.webapi_request(request)
                    if uinfo:
                        authorName = uinfo['response']['players'][0]['personaname']

                        i = 0
                        for level in data:
                            if len(data) > 2:
                                if level['author'] == ctx.author.id:
                                    i += 1
                            if level['level'].lower() == levelName.lower():
                                await ctx.send('Unable to add level due to {0} already being in the queue!'.format(levelName))
                                return
                    
                        if len(data) > int(self.user_count) - 1:
                            if i >= int(self.user_count):
                                await ctx.send('Unable to add level due to {0} already having {1} levels in the queue!'.format(ctx.author.display_name,self.user_count))
                                return

                        with open(path,'w') as outfile:
                            data.append({'link':levelLink,'level':levelName,'author':ctx.author.id,'nick':authorName,'twitch':ctx.author.display_name})
                            json.dump(data,outfile)
                        await ctx.send(f'Succesfully added {levelName} to the queue!')
                    else:
                        await ctx.send('Error with steam api')
                else:
                    await ctx.send('Error finding level, is the url correct?')
            else:
                await ctx.send('Error finding level, is the url correct?')
        else:
            await ctx.send('Invalid syntax, !add [level url]')
            
    @commands.command(name='remove',aliases=['delete'])
    async def remove(self,ctx):
        mat = search(r"\s(.+)",ctx.content)
        if mat:
            with open(path,'r') as infile:
                levels = json.load(infile)
            i = 0
            for level in levels:
                if level['level'].lower() == mat.group(1).lower():
                    if level['author'] == ctx.author.id:
                        levels.pop(i)
                        with open(path,'w') as outfile:
                            json.dump(levels, outfile)

                        await ctx.send(f'Succesfully removed {mat.group(1)} from list!')
                    else:
                        await ctx.send('Cannot remove level because {0} submitted it, not {1}.'.format(level['nick'], ctx.author.display_name))
                    break
                i += 1
        else:
            await ctx.send(f'Invalid syntax, !remove [link or level name]')
    
    @commands.command(name='list',aliases=['queue','q'])
    async def list(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        out = ""
        i = 1
        if len(levels) > 0:
            for level in levels:
                out += "{3} Level: '{0}' - Made by: '{1}' - Submitted by: '{2}'. ".format(level['level'],level['nick'],level['twitch'],i)
                i += 1
            await ctx.send(out)
        else:
            await ctx.send('The queue is currently empty.')

    @commands.command(name='clear',aliases=['reset','empty','init'])
    async def clear(self,ctx):
        if ctx.author.is_mod:
            with open(path,'w') as outfile:
                outfile.write('[]')
            with open(path2,'w') as outfile:
                outfile.write('')
            await ctx.send('Succesfully cleared queue!')

    @commands.command(name='current',aliases=['currentlevel','np','nowplaying','now'])
    async def current(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        if len(levels) > 0:
            await ctx.send('The current level is "{0}" by "{1}" submitted by "{2}" link {3}.'.format(levels[0]['level'],levels[0]['nick'],levels[0]['twitch'],levels[0]['link']))
        else:
            await ctx.send('The queue is currently empty.')


if len(argv) < 2:
    path = os.path.dirname(os.path.abspath(__file__)) + "/dir/levels.json"
else:
    path = argv[1]

if len(argv) < 3:
    path2 = os.path.dirname(os.path.abspath(__file__)) + "/dir/output.txt"
else:
    path2 = argv[2]

if len(argv) < 4:
    path3 = os.path.dirname(os.path.abspath(__file__)) + '/dir'
else:
    path3 = argv[3]

bot = Bot()

class run_bot(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        try:
            bot.run()
        finally:
            exit()

    def stop(self):
        bot.close()

class run_serv(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    def run(self):
        try:
            Handler = http.server.SimpleHTTPRequestHandler
            PORT = 8000
            os.chdir(str(path3))
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                httpd.serve_forever()
        finally:
            httpd.shutdown()
            exit()

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        # returns id of the respective thread
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)

def run_ui():
    root = tkinter.Tk()
    root.geometry("400x300")
    app = Window(root)
    root.mainloop()
    
if __name__ == '__main__':

    rbot = run_bot('twitch')
    rserv = run_serv('localhost')
    rui = threading.Thread(target=run_ui)
    rbot.start()
    time.sleep(1)
    rserv.start()
    rui.start()

    rui.join()
    print('ui ded')
    rserv.stop()
    rserv.join()
    print('serv ded')
    print('Close me pls')
