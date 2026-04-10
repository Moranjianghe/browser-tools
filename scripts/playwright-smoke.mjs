import { chromium } from 'playwright'
import { resolveBrowserBinary } from './common.mjs'

const executablePath = resolveBrowserBinary()
const url = process.argv[2] || 'https://example.com'

const browser = await chromium.launch({
  executablePath,
  headless: true,
})

try {
  const page = await browser.newPage()
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  console.log(`Title: ${await page.title()}`)
  console.log(`URL: ${page.url()}`)
} finally {
  await browser.close()
}

