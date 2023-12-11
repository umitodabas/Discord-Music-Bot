import discord
from discord.ext import commands
import yt_dlp

class Queue:
    def __init__(self):
        self.queue = []

    def add(self, url):
        self.queue.append(url)

    def remove(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def is_empty(self):
        return not bool(self.queue)

intents = discord.Intents.default()
intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
ydl = yt_dlp.YoutubeDL()

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')

queue = Queue()
ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

# Genel sohbet için kanal
general_channel_id = 1075465790452666380
general_channel = None

# Sadece botun mesajlarını göndermesi için kanal
bot_channel_id = 1075465790452666381
bot_channel = None

@bot.event
async def on_ready():
    global general_channel, bot_channel
    general_channel = bot.get_channel(general_channel_id)
    bot_channel = bot.get_channel(bot_channel_id)

    if not general_channel or not bot_channel:
        print("Channels not found. Please set correct channel IDs.")
        return

    print(f'Bot is ready! Logged in as {bot.user}')


@bot.command(name="play")
async def play(ctx, *, song_name: str):
    # Diğer kodlar...
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # İndirilen dosyaların konumu
    }

    await bot_channel.send(f"{song_name.capitalize()} adlı istek parçanız çalınıyor efendim.")

    url = None

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Şarkı ismini kullanarak YouTube'da arama yap
            info = ydl.extract_info(f"ytsearch:{song_name}", download=False)
            if 'entries' in info:
                url = info['entries'][0]['url']
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            await ctx.send(
                "Yürütülme esnasında bir hata oluştu. Müzik Botu çipçip sadece YouTube linklerini desteklemektedir.")
            return  # Hata durumunda fonksiyonu burada sonlandırın

    if url:
        # Bot zaten bir ses kanalında ise, mevcut bağlantıyı kullan
        if not ctx.voice_client:
            try:
                voice_channel = await ctx.author.voice.channel.connect()
            except Exception as e:
                print(f"An error occurred while connecting to the voice channel: {str(e)}")
                await ctx.send("An error occurred while connecting to the voice channel.")
                return  # Hata durumunda fonksiyonu burada sonlandırın

        # Şarkıyı sıraya ekleyin
        queue.add(url)

        # Eğer zaten bir şarkı çalıyorsa, sıradaki şarkıyı bekletin
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx)

        print(f"Added {song_name} to the queue.")
    else:
        await ctx.send("Vermiş olduğunuz URL bozuk.")
async def play_next(ctx):
    # Sıradaki şarkıyı çalın
    if not queue.is_empty():
        next_url = queue.remove()
        voice_channel = ctx.voice_client
        voice_channel.stop()
        voice_channel.play(discord.FFmpegPCMAudio(next_url, **ffmpeg_options),
                           after=lambda e: print('Player error: %s' % e) if e else None)
        print(f"Playing next audio from {next_url}")
    else:
        # Sıra boşsa kanaldan çıkın
        await ctx.voice_client.disconnect()
        print("Queue is empty. Disconnecting from the voice channel.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Botun kendi mesajlarına tepki verme

    if message.content.lower().startswith('!play'):
        # !play komutuna özel bir emoji ekleyerek mesajı düzenle
        emoji = "🎵"  # İstediğiniz emojiyi seçin
        await message.add_reaction(emoji)

    elif message.content.lower().startswith('speak'):
        # "speak" komutu ile belirli bir metni metin kanalına gönder
        text_to_speak = message.content[6:]  # "speak " kısmını atla
        await general_channel.send(text_to_speak)

    elif "search lyrics" in message.content.lower():
        # Şarkı sözleri aramasını yap ve sonucu kullanarak bir şarkı bul
        lyrics_query = message.content[14:]  # "search lyrics " kısmını atla
        song = await find_song(lyrics_query)
        if song:
            await play_song(general_channel, song)
        else:
            await general_channel.send("Şarkı bulunamadı.")

    await bot.process_commands(message)
async def find_song(lyrics_query):
    # Şarkı sözleri aramasını gerçekleştir ve bir şarkı nesnesi döndür
    # Bu fonksiyonun içeriği size bağlıdır ve şarkı sözlerini bir şarkıya çevirme işlemini gerçekleştirmelidir.
    # Örnek bir API veya kütüphane kullanabilirsiniz.
    return None  # Şarkı bulunamazsa None döndür

async def play_song(channel, song):
    # YouTube'da şarkıyı bul ve çalmak için play fonksiyonunu çağır
    # Bu fonksiyonun içeriği size bağlıdır ve bir YouTube API'si veya youtube_dl kütüphanesi kullanabilirsiniz.
    pass  # Bu fonksiyonu kendi ihtiyaçlarınıza göre doldurun

async def play_next(ctx):
    # Sıradaki şarkıyı çalın
    if not queue.is_empty():
        next_url = queue.remove()
        voice_channel = ctx.voice_client
        voice_channel.play(discord.FFmpegPCMAudio(next_url, **ffmpeg_options),
                           after=lambda e: print('Player error: %s' % e) if e else None)
        print(f"Playing next audio from {next_url}")

@bot.command(name="speak")
async def speak(ctx, *, message: str):
    # Botun belirli bir metni metin kanalına göndermesini sağla
    await general_channel.send(message)

@bot.command(name="join")
async def join(ctx):
    # Kullanıcının bulunduğu sesli kanala katıl
    channel = ctx.author.voice.channel
    await channel.connect()
    await general_channel.send(f"Joined {channel}")

@bot.command(name="leave")
async def leave(ctx):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_connected():
        await voice_channel.disconnect()
    await general_channel.send("Quited.")

@bot.command(name="skip")
async def skip(ctx):
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        voice_channel.stop()
        await ctx.send("Skipped.")
        await play_next(ctx)  # Yeni eklenen satır
    else:
        await general_channel.send("There is no song that can be skipped.")

@bot.command(name="pause")
async def pause(ctx):
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        voice_channel.pause()
        await general_channel.send("Stopped.")
    else:
        await general_channel.send("There is no song that can be stopped.")

@bot.command(name="stop")
async def pause(ctx):
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_playing():
        voice_channel.pause()
        await general_channel.send("Stopped.")
    else:
        await general_channel.send("There is no song that can be stopped.")

@bot.command(name="resume")
async def resume(ctx):
    voice_channel = ctx.voice_client
    if voice_channel and voice_channel.is_paused():
        voice_channel.resume()
        await general_channel.send("Resume")
    else:
        await general_channel.send("There is no song that can be resumed.")

@bot.command(name="volume")
async def volume(ctx, vol: int):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_channel.is_playing():
        voice_channel.source.volume = vol / 100  # 0.0 to 1.0 arasında bir değer bekler

        await general_channel.send(f"Volume seçeneğini {vol}% olarak ayarladınız fakat henüz bu özelliğimiz mevcut değil. Lütfen discord ses ayarından ses işlemlerinizi gerçekleştiriniz.")
    else:
        await general_channel.send("Nothing is currently playing.")


bot.run('Your Token')