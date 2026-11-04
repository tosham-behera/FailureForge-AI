export async function readLogFiles(files) {
  if (files.length > 4) throw new Error('Select at most 4 log files.')
  const sources = []
  let bytes = 0
  for (const file of files) {
    if (!/\.(log|txt)$/i.test(file.name) || /[/\\:]|\.\./.test(file.name) || file.name.length > 100) throw new Error('Only plain .log and .txt filenames are accepted.')
    if (file.size > 16384) throw new Error('Each file must be at most 16 KiB.')
    bytes += file.size
    if (bytes > 32768) throw new Error('Selected files exceed 32 KiB total.')
    let content
    try { content = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()) }
    catch { throw new Error('Log files must contain valid UTF-8 text.') }
    if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(content)) throw new Error('Binary content is not accepted.')
    if (!content.trim() || content.length > 12000) throw new Error('Each file must contain 1–12,000 characters of text.')
    if (sources.some(s => s.name === file.name)) throw new Error('Use unique filenames.')
    sources.push({ name: file.name, content })
  }
  return sources
}
