import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readLogFiles } from './uploads.js'
const file = (name, text) => ({name, size: Buffer.byteLength(text), arrayBuffer: async () => new TextEncoder().encode(text).buffer})
test('reads multiple chosen text files without losing names or lines', async () => {
  assert.deepEqual(await readLogFiles([file('app.log','error one\nerror two'),file('db.txt','stopped')]), [{name:'app.log',content:'error one\nerror two'},{name:'db.txt',content:'stopped'}])
})
test('rejects binary, invalid UTF-8, traversal, duplicates and limits', async () => {
  for (const files of [[file('a.py','error')], [file('../a.log','error')], [file('a.log','x\0y')], [file('a.log','x'.repeat(16385))], Array.from({length:5}, (_,i)=>file(`${i}.log`,'error')), [file('a.log','error'),file('a.log','other')], [{name:'a.log',size:1,arrayBuffer:async()=>new Uint8Array([255]).buffer}]]) {
    await assert.rejects(readLogFiles(files))
  }
})
