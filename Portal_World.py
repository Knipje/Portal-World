try:
    import http.server
    from twitchio.ext import commands
    from twitchio.errors import AuthenticationError,EchoMessageWarning
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
    input(str(e))
    exit()

class Window(tkinter.Frame):

    def __init__(self, master=None):
        with open(path3 + '/settings.txt', 'r') as infile:
            channel_name = infile.readlines()[2]
            mat = findall(r'"(.+?)"', channel_name)
            if len(mat) == 1:
                self.channel_name = mat[0]
            else:
                self.channel_name = None


        tkinter.Frame.__init__(self, master)
        self.master = master
        self.level = tkinter.StringVar(self, value='No levels in queue')
        self.twitch = tkinter.StringVar(self, value='No levels in queue')
        self.author = tkinter.StringVar(self, value='No levels in queue')
        self.link = tkinter.StringVar(self, value='No levels in queue')
        self.no_level = True
        with open(path,'r') as infile:
            self.update_texts(json.load(infile))
        self.init_window()

    def init_window(self):
        self.master.title("Portal World")
        self.pack(expand=1)
        tkinter.Label(self, text='Level name:').pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, textvariable=self.level, wraplength=390).pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, text='Level creator:').pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, textvariable=self.author, wraplength=390).pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, text='Level submitter:').pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, textvariable=self.twitch, wraplength=390).pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, text='Level link:').pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Label(self, textvariable=self.link, wraplength=390).pack(
            side="top", fill="both", pady=5, padx=2)
        tkinter.Button(self, text='Copy link', command=self.get_link).pack(
            side="top", fill="both", pady=5, padx=5)
        tkinter.Button(self, text='Next level', command=self.next).pack(
            side="top", fill="both", pady=5, padx=5)
        tkinter.Button(self, text="Input level manually", command=self.new_window).pack(
            side="top", fill="both", pady=5, padx=5)
        tkinter.Button(self, text="Clear list", command=self.clear_list).pack(
            side="top", fill="both", pady=5, padx=5)

    def new_window(self):
        self.t = tkinter.Toplevel(self)
        self.t.wm_title("Input level info")
        self.t.iconbitmap(favicon)
        tkinter.Label(self.t, text='Level name:').pack(
            side="top", fill="both", pady=5, padx=2)
        self.new_level = tkinter.StringVar(None)
        tkinter.Entry(self.t, textvariable=self.new_level).pack()
        tkinter.Label(self.t, text='Level creator:').pack(
            side="top", fill="both", pady=5, padx=2)
        self.new_creator = tkinter.StringVar(None)
        tkinter.Entry(self.t, textvariable=self.new_creator).pack()
        tkinter.Label(self.t, text='Level submitter:').pack(
            side="top", fill="both", pady=5, padx=2)
        self.new_submitter = tkinter.StringVar(None)
        if self.channel_name:
            self.new_submitter.set(self.channel_name)
        tkinter.Entry(self.t, textvariable=self.new_submitter).pack()
        tkinter.Label(self.t, text='Level link:').pack(
            side="top", fill="both", pady=5, padx=2)
        self.new_link = tkinter.StringVar(None)
        tkinter.Entry(self.t, textvariable=self.new_link).pack()
        tkinter.Button(self.t, text="Submit as next level", command=lambda: self.submit_new(
            True)).pack(side="top", fill="both", pady=5, padx=50)
        tkinter.Button(self.t, text="Submit to queue", command=lambda: self.submit_new(
            False)).pack(side="top", fill="both", pady=5, padx=50)
        tkinter.Button(self.t, text="Cancel", command=lambda: self.t.destroy()).pack(
            side="top", fill="both", pady=5, padx=50)

    def submit_new(self, top):
        self.t.destroy()
        level = self.new_level.get()
        creator = self.new_creator.get()
        submitter = self.new_submitter.get()
        link = self.new_link.get()
        if not level:
            level = "None"
        if not creator:
            creator = "None"
        if not submitter:
            submitter = "None"
        if not link:
            link = "None"
        with open(path, 'r') as infile:
            levelList = json.load(infile)
        out = {'level': level, 'twitch': submitter,
               'nick': creator, 'link': link}
        if len(levelList) > 0 and top:
            levelList.insert(1, out)
        else:
            levelList.append(out)
        with open(path, 'w') as outfile:
            json.dump(levelList, outfile)

    def update_texts(self,level):
        if len(level) == 0:
            self.level.set('No levels in queue')
            self.twitch.set('No levels in queue')
            self.author.set('No levels in queue')
            self.link.set('No levels in queue')
            self.no_level = False
        else:
            self.level.set(level[0]['level'])
            self.twitch.set(level[0]['twitch'])
            self.author.set(level[0]['nick'])
            self.link.set(level[0]['link'])
            self.no_level = True

    def clear_list(self):
        with open(path, 'w') as outfile:
            outfile.write('[]')
        self.update_texts([])

    def get_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.link.get())
        self.update()

    def next(self):
        with open(path,'r') as infile:
            levelList = json.load(infile)
        if len(levelList) >= 1 and self.no_level:
            # and str(levelList[0]['level']) == str(self.level.get())
            levelList.pop(0)
            self.count = False
            with open(path, 'w') as outfile:
                json.dump(levelList, outfile)
        self.update_texts(levelList)

    def stop(self):
        self.master.destroy()


class Bot(commands.Bot):

    def __init__(self):
        with open(path3 + '/def.txt','r') as infile:
            default = infile.read()
        with open(path3 + '/settings.txt', 'r') as infile:
            settings = infile.read()
            mat = findall(r'"(.+?)"', settings)
            if len(mat) < 5 or default == settings:
                print('Error, please fill settings.txt completely in first.')
                exit()
        self.move = False
        self.user_count = mat[3]
        self.settings = mat
        try:
            super().__init__(irc_token=mat[0],prefix=mat[4], nick=mat[1], initial_channels=[mat[2]])
        except AuthenticationError:
            print('settings.txt not filled in correctly. Please close this window and check you settings.')

    def close(self):
        os.system('exit')

    # Events don't need decorators when subclassed
    async def event_ready(self):
        print(f'Ready | {self.nick}')

    async def send_message(self,message,channel):
        if len(message) == 0 or message == None:
            return
        if len(message) < 500:
            await channel.send(message)
            return

        while len(message) >= 500:
            await channel.send(message[:499])
            message = message[499:]
        if len(message) != 0:
            await channel.send(message)

    async def event_message(self, message):
        try:
            if message.author == self.nick:
                return

            await self.handle_commands(message)

            await self.help_command(message)

        except Exception as e:
            if isinstance(e,commands.errors.CommandNotFound) or isinstance(e,EchoMessageWarning):
                return
            await message.channel.send("Uncaught error: {}".format(e))

    async def event_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound) or isinstance(error,EchoMessageWarning):
            return
        raise error

    async def help_command(self,ctx):
        if len(self.settings) >= 6:
            if ctx.content.startswith(str(self.settings[4]) + str(self.settings[5])):
                await self.send_message('{0}add[submit] (level url), {0}remove[/delete] (level name), {0}list[queue,q], {0}current[np]'.format(self.settings[4]),ctx)

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
                except Exception as e:
                    print("Failed to get level link, retrying... {}".format(e))
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
                            if level['link'].lower() == levelLink.lower():
                                await self.send_message('Unable to add level due to {0} already being in the queue!'.format(levelName),ctx)
                                return
                    
                        if len(data) > int(self.user_count) - 1:
                            if i >= int(self.user_count):
                                await self.send_message('Unable to add level due to {0} already having {1} levels in the queue!'.format(ctx.author.display_name,self.user_count),ctx)
                                return

                        with open(path,'w') as outfile:
                            data.append({'link':levelLink,'level':levelName,'author':ctx.author.id,'nick':authorName,'twitch':ctx.author.display_name})
                            json.dump(data,outfile)
                        await self.send_message(f'Succesfully added {levelName} to the queue!',ctx)
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
        mat = findall(r"""(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])""", ctx.content, IGNORECASE)
        if mat:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            i = 0
            for level in levels:
                if level['link'].lower() == mat.group(1).lower():
                    if level['author'] == ctx.author.id or ctx.author.is_mod:
                        if i == 0:
                            await ctx.send('Cannot remove level due to it currently being played.')
                        else:
                            lname = level['level']
                            levels.pop(i)
                            with open(path,'w') as outfile:
                                json.dump(levels, outfile)

                            await self.send_message(f'Succesfully removed {lname} from list!',ctx)
                    else:
                        await self.send_message('Cannot remove level because {0} submitted it, not {1}.'.format(level['twitch'], ctx.author.display_name),ctx)
                    break
                 
        else:
            mat = search(r"\s(.+)",ctx.content)
            if mat:
                with open(path,'r') as infile:
                    levels = json.load(infile)
                i = 0
                for level in levels:
                    if level['level'].lower() == mat.group(1).lower():
                        if level['author'] == ctx.author.id or ctx.author.is_mod:
                            if i == 0:
                                await ctx.send('Cannot remove level due to it currently being played.')
                            else:
                                lname = level['level']
                                levels.pop(i)
                                with open(path,'w') as outfile:
                                    json.dump(levels, outfile)

                                await self.send_message(f'Succesfully removed {lname} from list!',ctx)
                        else:
                            await self.send_message('Cannot remove level because {0} submitted it, not {1}.'.format(level['twitch'], ctx.author.display_name),ctx)
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
            await self.send_message(out,ctx)
        else:
            await ctx.send('The queue is currently empty.')

    @commands.command(name='mylist',aliases=['myqueue','myq','mq'])
    async def mylist(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        out = ""
        i = 1
        if len(levels) > 0:
            for level in levels:
                if level['author'] == ctx.author.id:
                    out += "{3} Level: '{0}' - Made by: '{1}' - Submitted by: '{2}'. ".format(level['level'],level['nick'],level['twitch'],i)
                i += 1
            if len(out) > 0:
                await self.send_message(out,ctx)
                await self.send_message('{} has no levels in the queue.'.format(ctx.author.display_name),ctx)
        else:
            await ctx.send('The queue is currently empty.')

    @commands.command(name='clear',aliases=['reset','empty','init'])
    async def clear(self,ctx):
        if ctx.author.is_mod:
            with open(path,'w') as outfile:
                outfile.write('[]')
            await ctx.send('Succesfully cleared queue!')

    @commands.command(name='current',aliases=['currentlevel','np','nowplaying','now'])
    async def current(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        if len(levels) > 0:
            await self.send_message('The current level is "{0}" by "{1}" submitted by "{2}" link {3}.'.format(levels[0]['level'],levels[0]['nick'],levels[0]['twitch'],levels[0]['link']),ctx)
        else:
            await ctx.send('The queue is currently empty.')


if len(argv) < 2:
    path = os.path.dirname(os.path.abspath(__file__)) + "/dir/levels.json"
else:
    path = argv[1]

if len(argv) < 3:
    path3 = os.path.dirname(os.path.abspath(__file__)) + '/dir'
else:
    path3 = argv[2]

favicon = os.path.dirname(os.path.abspath(__file__)) + '/imgs/favicon.ico'

with open(path3 + '/def.txt', 'r') as infile:
    default = infile.read()

with open(path3 + '/settings.txt', 'r') as infile:
    settings = infile.read()
    mat = findall(r'"(.+?)"', settings)
    if len(mat) < 5 or default == settings:
        input('Error, please fill settings.txt completely in first. ')
        exit()

class run_bot(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.bot = Bot()

    def run(self):
        try:
            self.bot.run()
        finally:
            exit()

    def stop(self):
        self.bot.close()

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
    root.iconbitmap(favicon)
    root.minsize(400,200)
    root.resizable(False, True)
    app = Window(root)
    app.mainloop()
    
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
