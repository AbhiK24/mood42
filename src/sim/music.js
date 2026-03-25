/**
 * Music Library - ambient tracks for mood42
 */

// Track library - expanded for channel diversity
// TODO: Replace placeholder files with actual royalty-free tracks
export const TRACKS = {
  // Lo-fi / Chill
  ambient1: {
    id: 'ambient1',
    name: 'Electronic Ambient',
    file: '/assets/ambient.mp3',
    mood: ['focused', 'neutral', 'productive'],
    tempo: 'medium',
    genre: 'electronic',
    source: 'SoundHelix',
  },
  lofi_night: {
    id: 'lofi_night',
    name: 'Late Night Lo-Fi',
    file: '/assets/ambient.mp3', // placeholder
    mood: ['focused', 'cozy', 'melancholic'],
    tempo: 'slow',
    genre: 'lo-fi',
    source: 'placeholder',
  },
  chillhop_rain: {
    id: 'chillhop_rain',
    name: 'Rainy Chillhop',
    file: '/assets/ambient.mp3',
    mood: ['cozy', 'focused', 'rainy'],
    tempo: 'slow',
    genre: 'chillhop',
    source: 'placeholder',
  },

  // Jazz
  jazz_piano: {
    id: 'jazz_piano',
    name: 'Coffee Shop Piano',
    file: '/assets/ambient.mp3',
    mood: ['cozy', 'warm', 'gentle'],
    tempo: 'medium',
    genre: 'jazz-piano',
    source: 'placeholder',
  },
  jazz_noir: {
    id: 'jazz_noir',
    name: 'Noir Saxophone',
    file: '/assets/ambient.mp3',
    mood: ['mysterious', 'melancholic', 'smoky'],
    tempo: 'slow',
    genre: '50s-jazz',
    source: 'placeholder',
  },
  smooth_jazz: {
    id: 'smooth_jazz',
    name: 'Smooth Evening Jazz',
    file: '/assets/ambient.mp3',
    mood: ['relaxed', 'warm', 'nostalgic'],
    tempo: 'medium',
    genre: 'jazz',
    source: 'placeholder',
  },

  // Synthwave / Retro
  synthwave_drive: {
    id: 'synthwave_drive',
    name: 'Neon Drive',
    file: '/assets/ambient.mp3',
    mood: ['energetic', 'driving', 'retro'],
    tempo: 'fast',
    genre: 'synthwave',
    source: 'placeholder',
  },
  retrowave: {
    id: 'retrowave',
    name: 'Retrowave Sunset',
    file: '/assets/ambient.mp3',
    mood: ['nostalgic', 'energetic', 'warm'],
    tempo: 'medium',
    genre: 'retrowave',
    source: 'placeholder',
  },

  // Ambient / Space
  space_drift: {
    id: 'space_drift',
    name: 'Deep Space Drift',
    file: '/assets/ambient.mp3',
    mood: ['transcendent', 'calm', 'vast'],
    tempo: 'glacial',
    genre: 'space-ambient',
    source: 'placeholder',
  },
  dark_ambient: {
    id: 'dark_ambient',
    name: 'Void',
    file: '/assets/ambient.mp3',
    mood: ['mysterious', 'deep', 'isolated'],
    tempo: 'glacial',
    genre: 'dark-ambient',
    source: 'placeholder',
  },

  // City Pop / Japanese
  citypop_night: {
    id: 'citypop_night',
    name: 'Tokyo Nights',
    file: '/assets/ambient.mp3',
    mood: ['urban', 'nostalgic', 'energetic'],
    tempo: 'medium',
    genre: 'city-pop',
    source: 'placeholder',
  },
  japanese_jazz: {
    id: 'japanese_jazz',
    name: 'Shinjuku Jazz',
    file: '/assets/ambient.mp3',
    mood: ['urban', 'cozy', 'warm'],
    tempo: 'medium',
    genre: 'japanese-jazz',
    source: 'placeholder',
  },

  // Acoustic / Morning
  acoustic_morning: {
    id: 'acoustic_morning',
    name: 'Sunday Guitar',
    file: '/assets/ambient.mp3',
    mood: ['hopeful', 'gentle', 'peaceful'],
    tempo: 'slow',
    genre: 'acoustic',
    source: 'placeholder',
  },
  indie_folk: {
    id: 'indie_folk',
    name: 'Golden Fields',
    file: '/assets/ambient.mp3',
    mood: ['hopeful', 'warm', 'nostalgic'],
    tempo: 'medium',
    genre: 'indie-folk',
    source: 'placeholder',
  },

  // Minimal / Focus
  minimal_focus: {
    id: 'minimal_focus',
    name: 'Pure Focus',
    file: '/assets/ambient.mp3',
    mood: ['productive', 'clean', 'steady'],
    tempo: 'steady',
    genre: 'minimal',
    source: 'placeholder',
  },
  post_rock: {
    id: 'post_rock',
    name: 'Distant Mountains',
    file: '/assets/ambient.mp3',
    mood: ['transcendent', 'building', 'emotional'],
    tempo: 'building',
    genre: 'post-rock',
    source: 'placeholder',
  },

  // Melancholy / Emotional
  sad_piano: {
    id: 'sad_piano',
    name: 'Empty Room',
    file: '/assets/ambient.mp3',
    mood: ['melancholic', 'sad', 'reflective'],
    tempo: 'slow',
    genre: 'sad-piano',
    source: 'placeholder',
  },
  emotional_strings: {
    id: 'emotional_strings',
    name: 'Fading Light',
    file: '/assets/ambient.mp3',
    mood: ['melancholic', 'emotional', 'beautiful'],
    tempo: 'slow',
    genre: 'strings',
    source: 'placeholder',
  },

  // Golden Hour / Warm
  dream_pop: {
    id: 'dream_pop',
    name: 'Hazy Sunset',
    file: '/assets/ambient.mp3',
    mood: ['nostalgic', 'warm', 'dreamy'],
    tempo: 'medium',
    genre: 'dream-pop',
    source: 'placeholder',
  },
  shoegaze: {
    id: 'shoegaze',
    name: 'Golden Blur',
    file: '/assets/ambient.mp3',
    mood: ['nostalgic', 'transcendent', 'warm'],
    tempo: 'medium',
    genre: 'shoegaze',
    source: 'placeholder',
  },
}

// Playlists by mood/time
export const PLAYLISTS = {
  night: ['lofi_night', 'jazz_noir', 'dark_ambient', 'sad_piano'],
  rain: ['chillhop_rain', 'jazz_piano', 'sad_piano'],
  focused: ['ambient1', 'minimal_focus', 'lofi_night'],
  melancholic: ['sad_piano', 'emotional_strings', 'jazz_noir'],
  cozy: ['jazz_piano', 'chillhop_rain', 'acoustic_morning'],
  energetic: ['synthwave_drive', 'citypop_night', 'retrowave'],
  transcendent: ['space_drift', 'dark_ambient', 'shoegaze', 'post_rock'],
  nostalgic: ['dream_pop', 'shoegaze', 'citypop_night', 'retrowave'],
  default: ['ambient1', 'lofi_night', 'jazz_piano'],
}

// Channel-to-playlist mapping
export const CHANNEL_PLAYLISTS = {
  ch01: ['lofi_night', 'chillhop_rain', 'ambient1'],           // Late Night
  ch02: ['jazz_piano', 'smooth_jazz', 'chillhop_rain'],       // Rain Cafe
  ch03: ['jazz_noir', 'smooth_jazz', 'sad_piano'],            // Jazz Noir
  ch04: ['synthwave_drive', 'retrowave'],                     // Synthwave
  ch05: ['space_drift', 'dark_ambient', 'post_rock'],         // Deep Space
  ch06: ['citypop_night', 'japanese_jazz', 'retrowave'],      // Tokyo Drift
  ch07: ['acoustic_morning', 'indie_folk', 'dream_pop'],      // Sunday Morning
  ch08: ['minimal_focus', 'ambient1', 'post_rock'],           // Focus
  ch09: ['sad_piano', 'emotional_strings', 'jazz_noir'],      // Melancholy
  ch10: ['dream_pop', 'shoegaze', 'indie_folk'],              // Golden Hour
}

// Music player state
let audio = null
let currentTrackId = null
let isPlaying = false
let volume = 0.3
let playlist = []
let playlistIndex = 0

/**
 * Initialize the music player
 */
export function initMusic() {
  audio = new Audio()
  audio.loop = true
  audio.volume = volume

  audio.addEventListener('ended', () => {
    // If not looping, go to next track
    if (!audio.loop && isPlaying) {
      nextTrack()
    }
  })

  audio.addEventListener('error', (e) => {
    console.error('[Music] Error loading track:', e)
  })

  return audio
}

/**
 * Load and play a track
 */
export function playTrack(trackId) {
  const track = TRACKS[trackId]
  if (!track) {
    console.error('[Music] Track not found:', trackId)
    return false
  }

  if (!audio) initMusic()

  audio.src = track.file
  currentTrackId = trackId

  return audio.play()
    .then(() => {
      isPlaying = true
      console.log('[Music] Playing:', track.name)
      return true
    })
    .catch(err => {
      console.error('[Music] Playback failed:', err)
      return false
    })
}

/**
 * Play a playlist
 */
export function playPlaylist(playlistName) {
  const tracks = PLAYLISTS[playlistName] || PLAYLISTS.default
  playlist = [...tracks]
  playlistIndex = 0

  if (playlist.length > 0) {
    return playTrack(playlist[0])
  }
  return Promise.resolve(false)
}

/**
 * Toggle play/pause
 */
export function toggle() {
  if (!audio) initMusic()

  if (isPlaying) {
    audio.pause()
    isPlaying = false
    return false
  } else {
    if (!currentTrackId && playlist.length === 0) {
      // Default to first track
      return playTrack('ambient1')
    }
    return audio.play()
      .then(() => {
        isPlaying = true
        return true
      })
      .catch(() => false)
  }
}

/**
 * Next track in playlist
 */
export function nextTrack() {
  if (playlist.length === 0) {
    playlist = Object.keys(TRACKS)
  }

  playlistIndex = (playlistIndex + 1) % playlist.length
  return playTrack(playlist[playlistIndex])
}

/**
 * Previous track
 */
export function prevTrack() {
  if (playlist.length === 0) {
    playlist = Object.keys(TRACKS)
  }

  playlistIndex = (playlistIndex - 1 + playlist.length) % playlist.length
  return playTrack(playlist[playlistIndex])
}

/**
 * Set volume (0-1)
 */
export function setVolume(v) {
  volume = Math.max(0, Math.min(1, v))
  if (audio) audio.volume = volume
  return volume
}

/**
 * Get current state
 */
export function getState() {
  const track = currentTrackId ? TRACKS[currentTrackId] : null
  return {
    isPlaying,
    currentTrack: track,
    volume,
    playlistIndex,
    playlistLength: playlist.length,
  }
}

/**
 * Get track info
 */
export function getTrackInfo(trackId) {
  return TRACKS[trackId] || null
}

/**
 * Get all tracks
 */
export function getAllTracks() {
  return Object.values(TRACKS)
}

/**
 * Add a new track to the library
 */
export function addTrack(track) {
  if (!track.id || !track.file) {
    console.error('[Music] Invalid track:', track)
    return false
  }

  TRACKS[track.id] = {
    id: track.id,
    name: track.name || track.id,
    file: track.file,
    mood: track.mood || ['neutral'],
    tempo: track.tempo || 'medium',
    source: track.source || 'unknown',
  }

  return true
}

/**
 * Get tracks by mood
 */
export function getTracksByMood(mood) {
  return Object.values(TRACKS).filter(track =>
    track.mood && track.mood.includes(mood)
  )
}

/**
 * Get tracks by genre
 */
export function getTracksByGenre(genre) {
  return Object.values(TRACKS).filter(track =>
    track.genre && track.genre.includes(genre)
  )
}

/**
 * Get tracks for a specific channel
 */
export function getTracksForChannel(channelId) {
  const trackIds = CHANNEL_PLAYLISTS[channelId] || PLAYLISTS.default
  return trackIds.map(id => TRACKS[id]).filter(Boolean)
}

/**
 * Get a random track for a channel
 */
export function getRandomTrackForChannel(channelId) {
  const tracks = getTracksForChannel(channelId)
  if (tracks.length === 0) return TRACKS.ambient1
  return tracks[Math.floor(Math.random() * tracks.length)]
}

/**
 * Play a random track for a channel
 */
export function playChannelMusic(channelId) {
  const track = getRandomTrackForChannel(channelId)
  return playTrack(track.id)
}
