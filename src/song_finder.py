import requests
from bs4 import BeautifulSoup
from mido import MidiFile


class SongFinder:
    def search_and_download_midi(self, query):
        search_url = f"https://bitmidi.com/search?q={query.replace(' ', '+')}"

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        # Send a GET request to the search URL with headers
        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find all anchor tags with class 'searchResult'
            search_results = soup.find_all('a', class_='pointer no-underline fw4 white underline-hover')

            if search_results:
                # Extract MIDI file URLs
                search_results = [(a.text, a['href']) for a in search_results]
                print(f"Found {len(search_results)} MIDI files:")
                # donwload the first midi file
                # TODO add a way to select which midi file to download
                return self._download_midi(f'https://bitmidi.com{search_results[0][1]}')
            else:
                print("No search results found.")
        else:
            print("Failed to retrieve search results.")


    def _download_midi(self, midi_url):

        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        # Send a GET request to the MIDI file URL with headers
        response = requests.get(midi_url, headers=headers)

        if response.status_code == 200:
            # find download link on page
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('h1', class_='mv3 f3').text

            # if the file already exists, don't download it again
            try:
                with open(f"../assets/midi/downloads/{title}", 'rb') as f:
                    print(f"MIDI file {title}.mid already exists.")
                    return MidiFile(f'../assets/midi/downloads/{title}')
            except:
                pass

            download_route = soup.find('a', {"download": f'{title}'})['href']
            download_url = f"https://bitmidi.com{download_route}"
            # Send a GET request to the download URL with headers
            response = requests.get(download_url, headers=headers)

            if response.status_code == 200:
                # Save the MIDI file to disk
                with open(f"../assets/midi/downloads/{title}", 'wb') as f:
                    f.write(response.content)
                    print(f"Downloaded MIDI file: {title}.mid")
                    return MidiFile(f'../assets/midi/downloads/{title}')
        else:
            print("Failed to download MIDI file.")


