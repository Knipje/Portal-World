try:
    import http.server
    from twitchio.ext import commands
    from twitchio.errors import AuthenticationError,EchoMessageWarning
    import json
    from re import search,findall,IGNORECASE,MULTILINE 
    from sys import argv
    import os
    import threading
    import time
    import requests
    import ctypes
    import steam
    import socketserver
    import webbrowser
except ImportError as e:
    input(str(e))
    exit()

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
        self.user_count = mat[3]
        self.settings = mat
        try:
            super().__init__(irc_token=mat[0],prefix=mat[5], nick=mat[1], initial_channels=[mat[2]])
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
        if len(self.settings) >= 7:
            if ctx.content.startswith(str(self.settings[5]) + str(self.settings[6])):
                await self.send_message('{0}add[submit] (level url), {0}remove[delete] (level name, url or id), {0}list[queue,q], {0}mylist[myqueue,myq], {0}current[np]'.format(self.settings[5]), ctx)

    # Commands use a different decorator
    @commands.command(name='add',aliases=['submit'])
    async def add(self, ctx):
        with open(path,'r') as infile:
            data = json.load(infile)
        try:
            if data[len(data) - 1] == False:
                await self.send_message("Couldn't add level due to the queue being locked",ctx)
                return
        except IndexError:
            pass

        mat = search(r"""(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])\?id=(\d*)""", ctx.content, IGNORECASE)
        if mat:
            levelLink = mat.string
            authId = mat.group(1)

            levelJson = steam.webapi.post(interface='ISteamRemoteStorage',method='GetPublishedFileDetails',params={'itemcount': 1, 'publishedfileids[0]':authId})
            
            if levelJson:
                levelName = levelJson['response']['publishedfiledetails'][0]['title']
                sId = levelJson['response']['publishedfiledetails'][0]['creator']

                uinfo = steam.webapi.get(interface='ISteamUser',method='GetPlayerSummaries',version=2,params={'key':'ABCE07D6D3E64ECBB4733E9E3DA30892','steamids':sId})
                if uinfo:
                    authorName = uinfo['response']['players'][0]['personaname']

                    i = 0
                    for level in data:
                        if len(data) > 2:
                            if level['twitchID'] == ctx.author.id:
                                i += 1
                        if level['link'].lower() == levelLink.lower():
                            await self.send_message('Unable to add level due to {0} already being in the queue!'.format(levelName),ctx)
                            return
                
                    if len(data) > int(self.user_count) - 1:
                        if i >= int(self.user_count):
                            await self.send_message('Unable to add level due to {0} already having {1} levels in the queue!'.format(ctx.author.display_name,self.user_count),ctx)
                            return

                    with open(path,'w') as outfile:
                        data.append({'link':levelLink,'levelName':levelName,'twitchID':ctx.author.id,'levelMakerName':authorName,'submitterName':ctx.author.display_name})
                        json.dump(data,outfile)
                    await self.send_message(f'Succesfully added {levelName} to the queue at place {len(data)}!',ctx)
                else:
                    await ctx.send('Error with steam api')
            else:
                await ctx.send('Error finding level, is the url correct?')
        else:
            mat = findall(f"{self.settings[5]}([\\w]+)\\s",ctx.content)
            if mat:
                await ctx.send(f'Invalid syntax, {self.settings[5]}{mat[0]} [level url]')
            else:
                await ctx.send('Invalid syntax.')
            
    @commands.command(name='remove', aliases=['delete'])
    async def remove(self, ctx):
        mat = findall(r"""(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])""", ctx.content, IGNORECASE)
        if mat:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            i = 0
            for level in levels:
                if level['link'].lower() == mat[0].lower():
                    if level['twitchID'] == ctx.author.id or ctx.author.is_mod:
                        if i == 0:
                            await ctx.send('Cannot remove level due to it currently being played.')
                        else:
                            lname = level['levelName']
                            levels.pop(i)
                            with open(path, 'w') as outfile:
                                json.dump(levels, outfile)

                            await self.send_message(f'Succesfully removed {lname} from list!', ctx)
                    else:
                        await self.send_message('Cannot remove level because {0} submitted it, not {1}.'.format(level['submitterName'], ctx.author.display_name), ctx)
                    break
                i += 1

        else:
            mat = search(r"\s(\d)", ctx.content)
            if mat:
                with open(path, 'r') as infile:
                    levels = json.load(infile)
                    i = int(mat.group(1)) - 1
                    if i == 0:
                        await ctx.send('Cannot remove level due to it currently being played.')
                    elif i + 1 > len(levels):
                        await ctx.send('Invalid level id')
                    else:
                        if level['twitchID'] == ctx.author.id or ctx.author.is_mod:
                            lname = level['levelName']
                            levels.pop(i)
                            with open(path, 'w') as outfile:
                                json.dump(levels, outfile)

                            await self.send_message(f'Succesfully removed {lname} from list!', ctx)
                        else:
                            await self.send_message('Cannot remove level because {0} submitted it, not {1}.'.format(level['submitterName'], ctx.author.display_name), ctx)
            else:
                mat = search(r"\s(.+)", ctx.content)
                if mat:
                    with open(path, 'r') as infile:
                        levels = json.load(infile)
                    i = 0
                    for level in levels:
                        if level['levelName'].lower() == mat.group(1).lower():
                            if level['twitchID'] == ctx.author.id or ctx.author.is_mod:
                                if i == 0:
                                    await ctx.send('Cannot remove level due to it currently being played.')
                                else:
                                    lname = level['levelName']
                                    levels.pop(i)
                                    with open(path, 'w') as outfile:
                                        json.dump(levels, outfile)
                                    await self.send_message(f'Succesfully removed {lname} from list!', ctx)
                            else:
                                await self.send_message('Cannot remove level because {0} submitted it, not {1}.'.format(level['submitterName'], ctx.author.display_name), ctx)
                            break
                        i += 1
                else:
                    mat = findall(f"{self.settings[5]}([\\w]+)\\s", ctx.content)
                    if mat:
                        await ctx.send(f'Invalid syntax, {self.settings[5]}{mat[0]} [link, level name or level id]')
                    else:
                        await ctx.send('You should not be seeing this, something went terribly wrong. Anyways, incorrect syntax.')
    
    @commands.command(name='promote')
    async def promote(self,ctx):
        mat = findall(r"""(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])""", ctx.content, IGNORECASE)
        if mat:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            i = 0
            for level in levels:
                if level['link'].lower() == mat[0].lower():
                    if ctx.author.is_mod:
                        if i == 0:
                            await ctx.send('Cannot promote level due to it currently being played.')
                        else:
                            lname = level['levelName']
                            levels.pop(i)
                            levels.insert(1, level)
                            with open(path, 'w') as outfile:
                                json.dump(levels, outfile)

                            await self.send_message(f'{lname} is now up next!', ctx)
                    break
                i += 1
        else:
            mat = search(r"\s(\d)", ctx.content)
            if mat:
                with open(path, 'r') as infile:
                    levels = json.load(infile)
                    i = int(mat.group(1)) - 1
                    if ctx.author.is_mod:
                        if i == 0:
                            await ctx.send('Cannot promote level due to it currently being played.')
                        elif i + 1 > len(levels):
                            await ctx.send('Invalid level id')
                        else:
                            level = levels[i]
                            lname = level['levelName']
                            levels.pop(i)
                            levels.insert(1, level)
                            with open(path, 'w') as outfile:
                                json.dump(levels, outfile)
                            await self.send_message(f'{lname} is now up next!', ctx)
            else:
                mat = search(r"\s(.+)", ctx.content)
                if mat:
                    with open(path, 'r') as infile:
                        levels = json.load(infile)
                    i = 0
                    for level in levels:
                        if level['levelName'].lower() == mat.group(1).lower():
                            if ctx.author.is_mod:
                                if i == 0:
                                    await ctx.send('Cannot promote level due to it currently being played.')
                                else:
                                    lname = level['levelName']
                                    levels.pop(i)
                                    levels.insert(1, level)
                                    with open(path, 'w') as outfile:
                                        json.dump(levels, outfile)

                                    await self.send_message(f'{lname} is now up next!', ctx)
                            break
                        i += 1
                else:
                    self.send_message(f'Invalid syntax: {self.settings[5]}promote [level name, url or id]',ctx)

    @commands.command(name='list',aliases=['queue','q'])
    async def list(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        out = ""
        i = 1
        if len(levels) > 0:
            if levels[len(levels) - 1] == False:
                levels = levels[:len(levels) - 1]
            if len(levels) <= int(self.settings[4]):
                for level in levels:
                    out += "{3} - Level: '{0}' - Made by: '{1}' - Submitted by: '{2}' ".format(level['levelName'],level['levelMakerName'],level['submitterName'],i)
                    i += 1
                await self.send_message(out,ctx)
            else:
                for level in levels:
                    if i <= int(self.settings[4]):
                        out += "{3} - Level: '{0}' - Made by: '{1}' - Submitted by: '{2}' ".format(level['levelName'],level['levelMakerName'],level['submitterName'],i)
                    i += 1
                if i > int(self.settings[4]):
                    ileft = i - int(self.settings[4])
                    out += f" And {ileft} more levels in queue."
                await self.send_message(out,ctx)
        else:
            await ctx.send('The queue is currently empty.')

    @commands.command(name='mylist',aliases=['myqueue','myq'])
    async def mylist(self,ctx):
        with open(path,'r') as infile:
            levels = json.load(infile)
        out = ""
        lInQueue = False
        i = 1
        if len(levels) > 0:
            if levels[len(levels) - 1] == False:
                levels = levels[:len(levels) - 1]
            if len(levels) <= int(self.settings[4]):
                for level in levels:
                    if level['twitchID'] == ctx.author.id:
                        out += "{3} - Level: '{0}' - Made by: '{1}' - Submitted by: '{2}' ".format(level['levelName'],level['levelMakerName'],level['submitterName'],i)
                        lInQueue = True
                    i += 1
                if out != "" and lInQueue:
                    await self.send_message(out,ctx)
                else:
                    await self.send_message('{} has no levels in the queue.'.format(ctx.author.display_name),ctx)
            else:
                for level in levels:
                    if i <= int(self.settings[4]):
                        if level['twitchID'] == ctx.author.id:
                            out += "{3} - Level: '{0}' - Made by: '{1}' - Submitted by: '{2}' ".format(level['levelName'],level['levelMakerName'],level['submitterName'],i)
                            lInQueue = True
                    else:
                        ileft = i - int(self.settings[4])
                        out += f" And {ileft} more levels in queue."
                        break
                    i += 1
                if out != "" and lInQueue:
                    await self.send_message(out,ctx)
                else:
                    await self.send_message('{} has no levels in the queue.'.format(ctx.author.display_name),ctx)
        else:
            await ctx.send('The queue is currently empty.')

    @commands.command(name='lock')
    async def lock(self, ctx):
        if ctx.author.is_mod:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            if len(levels) > 0:
                if levels[len(levels) - 1] == False:
                    await self.send_message('Queue was already locked', ctx)
                    return
                else:
                    levels.append(False)
                    with open(path, 'w') as outfile:
                        json.dump(levels, outfile)
                    await self.send_message('Succesfully locked queue', ctx)
            else:
                levels.append(False)
                with open(path, 'w') as outfile:
                    json.dump(levels, outfile)
                await self.send_message('Succesfully locked queue', ctx)

    @commands.command(name='unlock')
    async def unlock(self, ctx):
        if ctx.author.is_mod:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            if len(levels) > 0:
                if levels[len(levels) - 1] == False:
                    levels.pop(len(levels) - 1)
                    with open(path, 'w') as outfile:
                        json.dump(levels, outfile)
                    await self.send_message('Succesfully unlocked queue', ctx)
                else:
                    await self.send_message('Queue was already unlocked', ctx)
            else:
                await self.send_message('Queue was already unlocked', ctx)

    @commands.command(name='next', aliases=['skip'])
    async def next(self, ctx):
        if ctx.author.is_mod:
            with open(path, 'r') as infile:
                levels = json.load(infile)
            if len(levels) > 0:
                if levels[0] != False:
                    levels.pop(0)
                    with open(path, 'w') as outfile:
                        json.dump(levels, outfile)
                    await self.send_message('Succesfully skipped level', ctx)
                    return
            await self.send_message("Couldn't skip level due to the queue being empty", ctx)

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
        if len(levels) > 0 and levels[0] != False:
            await self.send_message('The current level is "{0}" by "{1}" submitted by "{2}" link {3}.'.format(levels[0]['levelName'],levels[0]['levelMakerName'],levels[0]['submitterName'],levels[0]['link']),ctx)
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
    if len(mat) < 6 or default == settings:
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

        class getHandler(http.server.SimpleHTTPRequestHandler):
            
            def do_GET(self):
                try:
                    http.server.SimpleHTTPRequestHandler.do_GET(self)
                except ConnectionAbortedError:
                    pass
                except FileNotFoundError:
                    pass
                try:
                    mat = findall(r"/dashboard.html\?removeLevelId=([\w]+)", self.path)
                    if mat:
                        try:
                            removeIndex = int(mat[0])
                        except ValueError:
                            if mat[0] == 'all':
                                with open(path,'w') as outfile:
                                    outfile.write('[]')
                            elif mat[0] == 'lock':
                                with open(path, 'r') as infile:
                                    levels = json.loads(infile.read())
                                    try:
                                        if levels[len(levels) - 1] == False:
                                            levels.pop(len(levels) - 1)
                                        else:
                                            levels.append(False)
                                    except IndexError:
                                        levels.append(False)
                                    with open(path, 'w') as outfile:
                                        json.dump(levels, outfile)
                        else:
                            with open(path,'r') as infile:
                                levels = json.load(infile)
                            if levels[removeIndex] != False:
                                levels.pop(removeIndex)
                            with open(path,'w') as outfile:
                                json.dump(levels,outfile)
                    else:
                        mat = findall(r"/dashboard.html\?promoteLevelId=([\w]+)", self.path)
                        if mat:
                            with open(path, 'r') as infile:
                                levels = json.load(infile)
                                i = int(mat[0]) - 1
                                if i != 0 or i + 1 < len(levels):
                                    level = levels[i]
                                    levels.pop(i)
                                    levels.insert(1, level)
                                    with open(path, 'w') as outfile:
                                        json.dump(levels, outfile)

                        mat = findall(r"\/dashboard\.html\?levelName=(.*?)&levelMakerName=(.*?)&submitterName=(.*?)&link=(.*?)&d=", self.path)
                        if mat:
                            link = mat[0][3]
                            levelName = mat[0][0].replace('+',' ')
                            levelMakerName = mat[0][1].replace('+', ' ')
                            submitterName = mat[0][2].replace('+', ' ')
                            
                            l = {'link':link,'levelName':levelName,'twitchID':None,'levelMakerName':levelMakerName,'submitterName':submitterName}
                            with open(path,'r') as infile:
                                levels = json.load(infile)
                            levels.append(l)
                            with open(path,'w') as outfile:
                                json.dump(levels,outfile)

                except Exception:
                    pass

            def do_HEAD(self):
                http.server.SimpleHTTPRequestHandler.do_HEAD(self)

            def log_message(self, format, *args):
                return

            def log_error(self, format, *args):
                return

        try:
            Handler = getHandler
            PORT = 8000
            os.chdir(str(path3))
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                httpd.serve_forever()
        finally:
            while True:
                try:
                    httpd.shutdown()
                except Exception:
                    pass
                else:
                    break
            exit()

    def get_id(self):
        # returns id of the respective thread
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)

if __name__ == '__main__':

    rbot = run_bot('twitch')
    rserv = run_serv('localhost')
    rbot.start()
    rserv.start()
    time.sleep(1)
    webbrowser.open('http://localhost:8000/dashboard.html')
