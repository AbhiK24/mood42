/**
 * Music Library - ambient tracks for mood42
 */

// Track library
export const TRACKS = {
  ambient1: {
    id: 'ambient1',
    name: 'Electronic Ambient',
    file: '/assets/ambient.mp3',
    mood: ['focused', 'neutral'],
    tempo: 'medium',
    source: 'SoundHelix',
  },
  // Add more tracks here as we find them
}

// Playlists by mood/time
export const PLAYLISTS = {
  night: ['ambient1'],
  rain: ['ambient1'],
  focused: ['ambient1'],
  melancholic: ['ambient1'],
  default: ['ambient1'],
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
