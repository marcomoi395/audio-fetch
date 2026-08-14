import { access } from 'node:fs/promises'
import { constants } from 'node:fs'
import { join } from 'node:path'
import process from 'node:process'

const artifactFlag = process.argv.indexOf('--artifact-root')
const artifactRoot = artifactFlag >= 0 ? process.argv[artifactFlag + 1] : undefined
if (artifactFlag >= 0 && !process.argv[artifactFlag + 1]) {
  throw new Error('--artifact-root requires a directory')
}
const platformPackage = `${process.platform === 'win32' ? 'win32' : process.platform}-${process.arch}`
const executable = process.platform === 'win32' ? 'yt-dlp.exe' : 'yt-dlp'
const ffmpegExecutable = process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg'
const root = artifactRoot ? join(artifactRoot, 'resources', 'app.asar.unpacked') : process.cwd()
const packageRoot = join(root, 'node_modules')
const paths = [
  join(packageRoot, 'youtube-dl-exec', 'bin', executable),
  join(packageRoot, '@ffmpeg-installer', platformPackage, ffmpegExecutable)
]

for (const path of paths) {
  await access(path, constants.X_OK)
  console.log(`resource ok: ${path}`)
}
