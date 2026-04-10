import { chromium } from 'playwright'
import { resolveCdpUrl } from './common.mjs'

const cdpUrl = resolveCdpUrl()
const url = process.argv[2] || 'https://example.com'

console.log(`Connecting to ${cdpUrl}`)

const browser = await chromium.connectOverCDP(cdpUrl)

try {
  const context = browser.contexts()[0] || (await browser.newContext())
  const page = await context.newPage()
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  console.log(`Title: ${await page.title()}`)
  console.log(`URL: ${page.url()}`)
} finally {
  await browser.close()
}

