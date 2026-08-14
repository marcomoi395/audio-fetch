import { describe, expect, it } from 'vitest'
import {
  configurePackagedYtDlpEnvironment,
  resolvePackagedFfmpegPath,
  resolvePackagedYtDlpPath,
  resolveFfmpegPath
} from '../../src/main/utils/binaries'

describe('packaged binary paths', () => {
  it('resolves yt-dlp inside Electron asarUnpack output', () => {
    expect(resolvePackagedYtDlpPath('/opt/audio-fetch/resources')).toBe(
      '/opt/audio-fetch/resources/app.asar.unpacked/node_modules/youtube-dl-exec/bin/yt-dlp'
    )
  })

  it('preserves existing youtube-dl-exec environment settings', () => {
    const env: NodeJS.ProcessEnv = {
      YOUTUBE_DL_DIR: '/existing/bin',
      YOUTUBE_DL_FILENAME: 'custom-yt-dlp'
    }

    expect(configurePackagedYtDlpEnvironment('/opt/audio-fetch/resources', env, () => true)).toBe(
      true
    )
    expect(env).toEqual({ YOUTUBE_DL_DIR: '/existing/bin', YOUTUBE_DL_FILENAME: 'custom-yt-dlp' })
  })

  it('leaves environment unchanged when the packaged binary is missing', () => {
    const env: NodeJS.ProcessEnv = {}

    expect(configurePackagedYtDlpEnvironment('/opt/audio-fetch/resources', env, () => false)).toBe(
      false
    )
    expect(env).toEqual({})
  })
  it('resolves packaged FFmpeg inside Electron asarUnpack output', () => {
    expect(resolvePackagedFfmpegPath('/opt/audio-fetch/resources')).toBe(
      '/opt/audio-fetch/resources/app.asar.unpacked/node_modules/@ffmpeg-installer/linux-x64/ffmpeg'
    )
  })

  it('uses packaged FFmpeg when available and falls back otherwise', () => {
    const packagedPath = resolvePackagedFfmpegPath('/opt/audio-fetch/resources')

    expect(resolveFfmpegPath('/opt/audio-fetch/resources', '/dev/ffmpeg', () => true)).toBe(
      packagedPath
    )
    expect(resolveFfmpegPath('/opt/audio-fetch/resources', '/dev/ffmpeg', () => false)).toBe(
      '/dev/ffmpeg'
    )
  })
})
