"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import axios from "axios";

export default function Home() {
  const [userSearch, setUserSearch] = useState("");
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentState, setCurrentState] = useState<string>("search");
  const [availableSongs, setAvailableSongs] = useState<string[]>([]);
  // const apiURL = "https://9156-199-111-224-2.ngrok-free.app";
  const apiURL = "http://localhost:5000";

  // demoing recording feedback done
  useEffect(() => {
    // call this function every second
    console.log("here");
    const interval = setInterval(() => {
      axios.get(`${apiURL}/getState`).then((response: any) => {
        setCurrentState(response.data.state);
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    console.log("here");
    axios.get(`${apiURL}/availableSongs`).then((response: any) => {
      setAvailableSongs(response.data.songs);
    });
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    const response = await fetch(`${apiURL}/search?query=${userSearch}`);
    const data = await response.json();
    console.log(data);
    setSearchResults(data.results.slice(0, 7));
    setLoading(false);
  };

  const handleSelectSong = async (song_url: string, song_file_name: string) => {
    setLoading(true);
    const response = await fetch(
      `${apiURL}/setSong?song_url=${song_url}&song_file_name=${song_file_name}`
    );
    const data = await response.json();
    console.log(data);
    setLoading(false);
  };

  const handleSelectLocalSong = async (song_file_name: string) => {
    setLoading(true);
    const response = await fetch(
      `${apiURL}/setLocalSong?song_file_name=${song_file_name}`
    );
    const data = await response.json();
    console.log(data);
    setLoading(false);
  };

  const handleSetState = async (state: string) => {
    setLoading(true);
    const response = await fetch(`${apiURL}/setState?state=${state}`);
    const data = await response.json();
    console.log(data);
    setLoading(false);
  };

  // return <div className="text-white">{currentState}</div>;
  if (currentState === "search") {
    return (
      <main className="flex h-screen flex-col items-center justify-center p-24">
        <div className="flex flex-col items-center">
          <h1 className="text-4xl font-bold">Search for a Song!</h1>
          <input
            className="w-96 p-2 mt-4 text-black border border-gray-300 rounded"
            type="text"
            placeholder="Search for a song you would like to learn!"
            value={userSearch}
            onChange={(e) => setUserSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch();
              }
            }}
          />
          <h2 className="mt-4 text-lg">Available Songs</h2>
          {searchResults.length == 0 &&
            availableSongs.map((song) => (
              <div
                key={song}
                className="mt-4 p-2 text-black bg-gray-100 rounded"
                onClick={() => {
                  handleSelectLocalSong(song);
                }}
              >
                {song}
              </div>
            ))}
          <button
            className="mt-4 p-2 bg-blue-500 text-white rounded"
            onClick={async () => {
              handleSearch();
            }}
          >
            Search
          </button>
          {searchResults.map((result) => (
            <div
              key={result}
              className="mt-4 p-2 text-black bg-gray-100 rounded"
              onClick={() => {
                handleSelectSong(result[1], result[0]);
              }}
            >
              {result[0]}
            </div>
          ))}
        </div>
      </main>
    );
  }

  if (currentState === "song_set") {
    return (
      <div className="flex h-screen flex-col items-center justify-center p-24 text-white">
        <h1 className="text-4xl font-bold">Song Set!</h1>
        <div className="mt-4 p-2 text-black bg-gray-100 rounded">
          Song Selected! Let me know when you want to start!
        </div>
        <button
          className="mt-4 p-2 bg-blue-500 text-white rounded"
          onClick={() => handleSetState("teach")}
        >
          Start Song
        </button>
      </div>
    );
  }

  if (currentState === "instructor") {
    return (
      <div
        onClick={() => setCurrentState("player")}
        className="flex h-screen max-h-screen flex-col items-center justify-center text-3xl p-24 text-white"
      >
        Repeat After Me 🎹 😃
      </div>
    );
  }
  if (currentState === "player") {
    return (
      <div className="flex h-screen max-h-screen flex-col items-center justify-center text-3xl p-24 text-white">
        Now You Try! 🎹 😃
      </div>
    );
  }
}
