import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, describe, expect, it } from 'vitest'
import {
  configurePackagedYtDlpEnvironment,
  prepareYtDlpRuntime,
  resolvePackagedFfmpegPath,
  resolvePackagedYtDlpPath,
  resolveUserYtDlpPath,
  resolveYtDlpSourcePath,
  resolveFfmpegPath
} from '../../src/main/utils/binaries'

const temporaryDirectories: string[] = []

afterEach(async () => {
  await Promise.all(
    temporaryDirectories.splice(0).map((directory) => rm(directory, { recursive: true }))
  )
})

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
  it('resolves development and user-writable yt-dlp paths', () => {
    expect(resolveYtDlpSourcePath(undefined, '/workspace/audio-fetch', false)).toBe(
      '/workspace/audio-fetch/node_modules/youtube-dl-exec/bin/yt-dlp'
    )
    expect(resolveUserYtDlpPath('/home/user/.config/audio-fetch')).toBe(
      '/home/user/.config/audio-fetch/yt-dlp/yt-dlp'
    )
  })

  it('copies the packaged binary into the user-writable runtime directory', async () => {
    const directory = await mkdtemp(join(tmpdir(), 'audio-fetch-'))
    temporaryDirectories.push(directory)
    const sourcePath = join(directory, 'source-yt-dlp')
    const userDataPath = join(directory, 'user-data')
    await writeFile(sourcePath, 'binary')

    const runtime = await prepareYtDlpRuntime(sourcePath, userDataPath)

    expect(runtime.binaryPath).toBe(resolveUserYtDlpPath(userDataPath))
    expect(await readFile(runtime.binaryPath, 'utf8')).toBe('binary')
    expect(runtime.updatePath).toBe(runtime.binaryPath)
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
