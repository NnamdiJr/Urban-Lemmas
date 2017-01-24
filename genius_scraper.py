import requests
from bs4 import BeautifulSoup
import re
import os


def create_artist_list(text_file):
    artists = []

    with open(text_file) as f:
        for line in f:
            artists.append(line.split(', ')[1].strip())

    return sorted(artists)


def get_artist_pages_popular(artist):
    print "Getting {} artist page from popular index...".format(artist)

    first_char = artist[0]

    if first_char.isdigit():
        r_pop = requests.get("https://genius.com/artists-index/0").content
    elif first_char.isalpha():
        r_pop = requests.get("https://genius.com/artists-index/" + first_char.lower()).content
    else:
        r_pop = requests.get("https://genius.com/artists-index/" + artist[1].lower()).content

    soup1 = BeautifulSoup(r_pop, "html.parser")

    artist_link = soup1.findAll('a', text=artist)

    if artist_link:
        return artist_link[0]['href']
    else:
        return get_artist_pages_all(artist)


def get_artist_pages_all(artist):
    print "{} not found on popular index \nSearching all index instead...".format(artist)

    first_char = artist[0]

    if first_char.isdigit():
        url = "https://genius.com/artists-index/0/all"
    elif first_char.isalpha():
        url = "https://genius.com/artists-index/" + first_char.lower() + '/all'
    else:
        url = "https://genius.com/artists-index/" + artist[1].lower() + '/all'

    r_all_a = requests.get(url).content
    soup_a = BeautifulSoup(r_all_a, "html.parser")

    artist_index_page = 1
    artist_end_page = soup_a.findAll("div", {"class": "pagination"})[0].text.split()[-3]

    while artist_index_page <= int(artist_end_page):
        r_all_b = requests.get(url + '?page=' + str(artist_index_page)).content
        soup_b = BeautifulSoup(r_all_b, "html.parser")
        artist_link = soup_b.findAll('a', text=artist)

        if artist_link:
            return artist_link[0]['href']

        artist_index_page += 1


def get_artist_songs(artist, artistLink):
    print "Getting {} song links...".format(artist)

    r2 = requests.get(artistLink).content
    soup2 = BeautifulSoup(r2, "html.parser")

    all_songs_link = soup2.findAll('a', href=re.compile('^/artists/song?'))

    if not all_songs_link:
        artist_songs_list = [song.a['href'] for song in soup2.findAll("div", {"class": "mini_card_grid-song"})]

    else:
        all_songs_link = all_songs_link[0]['href']

        r3 = requests.get("https://genius.com" + all_songs_link).content
        soup3 = BeautifulSoup(r3, "html.parser")

        artist_songs_list = []
        songs_index_page = 1
        songs_end_page = soup3.findAll("div", {"class": "pagination"})[0].text.split()[-3]

        while songs_index_page <= int(songs_end_page):
            r4 = requests.get("https://genius.com" + all_songs_link + '&page=' + str(songs_index_page)).content
            soup4 = BeautifulSoup(r4, "html.parser")
            stuff = [song.a['href'] for song in soup4.findAll("li", {"data-id" : re.compile('[0-9]')})]
            artist_songs_list.extend(stuff)

            songs_index_page += 1

    print "Finishing up {} song links...".format(artist)

    return artist_songs_list


def create_lyrics_files(artist, songsList):
    print "Creating {} directory and saving songs to html...".format(artist)

    for song_link in songsList:
        song = song_link.split('/')[-1].replace('-', '_')

        r5 = requests.get(song_link).content
        soup5 = BeautifulSoup(r5, "html.parser")

        with open('data/' + artist + '/' + song + '.html', 'w') as f:
            print "Writing html file for {} song: {}".format(artist, song)
            f.write(str(soup5))

    print "Finished {}!".format(artist)

if __name__ == "__main__":
    artists_list = create_artist_list('data/Test.txt')
    for one_artist in artists_list:
        artist_name = one_artist.replace(" ", "_")
        artist_page_links = get_artist_pages_popular(one_artist)
        if artist_page_links is None:
            print "{} is not an artist in Genius database...\nMoving on to next artist.".format(one_artist)
            continue
        artist_song_list = get_artist_songs(artist_name, artist_page_links)
        os.mkdir("data/" + artist_name)
        create_lyrics_files(artist_name, artist_song_list)