"use client"

import { useState, useEffect } from "react"
import { Gamepad2, Trophy, XCircle, HelpCircle } from "lucide-react"
import { fightersAPI, wordleAPI, type FighterBase, type WordleGuessResponse, type WordleFighter } from "@/lib/api"
import Image from "next/image"

interface GameState {
  guesses: WordleGuessResponse[];
  gameOver: boolean;
  won: boolean;
  target?: WordleFighter;
}

const MAX_GUESSES = 6;

export default function FighterWordlePage() {
  const [gameState, setGameState] = useState<GameState>({
    guesses: [],
    gameOver: false,
    won: false,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<FighterBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [hint, setHint] = useState("");
  const [showHelp, setShowHelp] = useState(false);

  // Load game state from localStorage
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const saved = localStorage.getItem(`wordle_${today}`);
    if (saved) {
      setGameState(JSON.parse(saved));
    }

    // Load hint
    wordleAPI.getDaily().then(data => {
      setHint(data.hint);
    }).catch(err => {
      console.error("Error loading hint:", err);
    });
  }, []);

  // Save game state to localStorage
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    localStorage.setItem(`wordle_${today}`, JSON.stringify(gameState));
  }, [gameState]);

  const searchFighters = async (term: string) => {
    if (term.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const data = await fightersAPI.list({ search: term, page_size: 10 });
      setSearchResults(data.fighters);
    } catch (err) {
      console.error("Error searching fighters:", err);
    }
  };

  const handleGuess = async (fighter: FighterBase) => {
    if (gameState.gameOver || gameState.guesses.length >= MAX_GUESSES) return;

    setLoading(true);
    setSearchTerm("");
    setSearchResults([]);

    try {
      const result = await wordleAPI.submitGuess(fighter.id);

      const newGuesses = [...gameState.guesses, result];
      const won = result.correct;
      const gameOver = won || newGuesses.length >= MAX_GUESSES;

      setGameState({
        guesses: newGuesses,
        gameOver,
        won,
        target: result.target,
      });

      // If game over and lost, reveal answer
      if (gameOver && !won) {
        const answer = await wordleAPI.reveal();
        setGameState(prev => ({ ...prev, target: answer }));
      }
    } catch (err) {
      console.error("Error submitting guess:", err);
    } finally {
      setLoading(false);
    }
  };

  const remainingGuesses = MAX_GUESSES - gameState.guesses.length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="flex items-center gap-3 text-4xl font-bold">
            <Gamepad2 className="h-10 w-10" />
            Fighter Wordle
          </h1>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="rounded-lg border bg-card p-2 transition-all hover:bg-muted"
          >
            <HelpCircle className="h-6 w-6" />
          </button>
        </div>
        <p className="text-muted-foreground">
          Guess the UFC fighter in {MAX_GUESSES} attempts. Use the hints to narrow it down!
        </p>
        {hint && (
          <div className="rounded-lg border-l-4 border-blue-500 bg-blue-500/10 p-4">
            <p className="text-sm"><strong>Hint:</strong> {hint}</p>
          </div>
        )}
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 text-xl font-bold">How to Play</h3>
          <div className="space-y-3 text-sm">
            <p>Guess the UFC fighter in {MAX_GUESSES} tries. After each guess, you'll get hints:</p>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🟩</span>
                <span><strong>Green:</strong> Exact match</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">🟨</span>
                <span><strong>Yellow:</strong> Close (adjacent weight class or within 3 years age)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">⬜</span>
                <span><strong>White:</strong> Incorrect</span>
              </div>
            </div>
            <p className="mt-4"><strong>Hints:</strong> Weight class, nationality, and age range</p>
          </div>
        </div>
      )}

      {/* Game Over Message */}
      {gameState.gameOver && (
        <div className={`rounded-lg border p-6 ${gameState.won ? 'border-green-500 bg-green-500/10' : 'border-red-500 bg-red-500/10'}`}>
          <div className="flex items-center gap-3">
            {gameState.won ? (
              <Trophy className="h-8 w-8 text-green-500" />
            ) : (
              <XCircle className="h-8 w-8 text-red-500" />
            )}
            <div>
              <h3 className="text-xl font-bold">
                {gameState.won ? `Congratulations! You won in ${gameState.guesses.length} ${gameState.guesses.length === 1 ? 'guess' : 'guesses'}!` : 'Game Over!'}
              </h3>
              {gameState.target && (
                <p className="mt-2">
                  The answer was <strong>{gameState.target.name}</strong>
                  {gameState.target.weight_class && ` (${gameState.target.weight_class})`}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Search Box */}
      {!gameState.gameOver && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 text-lg font-semibold">
            Guess {gameState.guesses.length + 1} of {MAX_GUESSES}
          </h3>
          <div className="relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                searchFighters(e.target.value);
              }}
              placeholder="Search for a fighter..."
              disabled={loading}
              className="w-full rounded-lg border bg-background px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />

            {searchResults.length > 0 && (
              <div className="absolute z-10 mt-2 w-full rounded-lg border bg-card shadow-lg">
                {searchResults.map((fighter) => (
                  <button
                    key={fighter.id}
                    onClick={() => handleGuess(fighter)}
                    disabled={loading}
                    className="flex w-full items-center gap-3 border-b p-3 transition-all hover:bg-muted last:border-b-0 disabled:opacity-50"
                  >
                    <div className="relative h-12 w-12 overflow-hidden rounded-full">
                      {fighter.image_url ? (
                        <Image
                          src={fighter.image_url}
                          alt={fighter.name}
                          fill
                          className="object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-muted">
                          <Gamepad2 className="h-6 w-6 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="text-left">
                      <div className="font-semibold">{fighter.name}</div>
                      {fighter.weight_class && (
                        <div className="text-sm text-muted-foreground">{fighter.weight_class}</div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="mt-4 text-sm text-muted-foreground">
            {remainingGuesses} {remainingGuesses === 1 ? 'guess' : 'guesses'} remaining
          </div>
        </div>
      )}

      {/* Guesses */}
      {gameState.guesses.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-bold">Your Guesses</h3>
          {gameState.guesses.map((guess, index) => (
            <GuessCard key={index} guess={guess} guessNumber={index + 1} />
          ))}
        </div>
      )}

      {/* Answer Reveal */}
      {gameState.gameOver && gameState.target && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 text-xl font-bold">The Answer</h3>
          <div className="flex items-center gap-4">
            {gameState.target.image_url && (
              <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-primary">
                <Image
                  src={gameState.target.image_url}
                  alt={gameState.target.name}
                  fill
                  className="object-cover"
                />
              </div>
            )}
            <div>
              <h4 className="text-2xl font-bold">{gameState.target.name}</h4>
              {gameState.target.weight_class && (
                <p className="text-muted-foreground">{gameState.target.weight_class}</p>
              )}
              <div className="mt-2 flex gap-4 text-sm">
                {gameState.target.nationality && (
                  <span>🌍 {gameState.target.nationality}</span>
                )}
                {gameState.target.age && (
                  <span>🎂 {gameState.target.age} years old</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function GuessCard({ guess, guessNumber }: { guess: WordleGuessResponse; guessNumber: number }) {
  return (
    <div className={`rounded-lg border p-4 ${guess.correct ? 'border-green-500 bg-green-500/10' : 'bg-card'}`}>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold text-muted-foreground">Guess #{guessNumber}</span>
        {guess.correct && (
          <span className="rounded-full bg-green-500 px-3 py-1 text-xs font-bold text-white">
            CORRECT!
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {guess.guess.image_url && (
          <div className="relative h-16 w-16 overflow-hidden rounded-full">
            <Image
              src={guess.guess.image_url}
              alt={guess.guess.name}
              fill
              className="object-cover"
            />
          </div>
        )}
        <div className="flex-1">
          <h4 className="text-lg font-bold">{guess.guess.name}</h4>
          {guess.guess.weight_class && (
            <p className="text-sm text-muted-foreground">{guess.guess.weight_class}</p>
          )}
        </div>
      </div>

      {!guess.correct && (
        <div className="mt-4 grid grid-cols-3 gap-3">
          <HintBox label="Weight Class" hint={guess.hints.weight_class} value={guess.guess.weight_class} />
          <HintBox label="Nationality" hint={guess.hints.nationality} value={guess.guess.nationality} />
          <HintBox label="Age" hint={guess.hints.age} value={guess.guess.age?.toString()} />
        </div>
      )}
    </div>
  );
}

function HintBox({ label, hint, value }: { label: string; hint: string; value?: string }) {
  return (
    <div className="rounded-lg border bg-muted p-3 text-center">
      <div className="mb-1 text-xs text-muted-foreground">{label}</div>
      <div className="mb-1 text-2xl">{hint}</div>
      <div className="text-xs font-semibold">{value || "N/A"}</div>
    </div>
  );
}
