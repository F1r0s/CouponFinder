const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log('Starting Groupon scraper...');
    const browser = await puppeteer.launch({
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        headless: 'new'
    });
    const page = await browser.newPage();

    // Set a realistic user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36');

    try {
        await page.goto('https://www.groupon.com/coupons', { waitUntil: 'networkidle2', timeout: 60000 });

        const coupons = await page.evaluate(() => {
            const results = [];
            // This selector is a best-effort approach as Groupon's DOM changes frequently.
            // Adjust selectors based on actual site structure if this fails.
            const items = document.querySelectorAll('div[data-bhw="StoreCard"], .coupon-tile, .c-card');

            items.forEach((item, index) => {
                if (index > 15) return; // Limit to ~15 coupons so we don't overload the UI

                const titleEl = item.querySelector('h3, .title, .offer-title');
                const title = titleEl ? titleEl.innerText.trim() : 'Special Deal';

                const brandEl = item.querySelector('.merchant-name, .brand-name');
                const brand = brandEl ? brandEl.innerText.trim() : 'Groupon Deal';

                const descEl = item.querySelector('.description, .offer-description');
                const description = descEl ? descEl.innerText.trim() : 'Claim this special offer on Groupon today.';

                // Construct standard object for couponsData
                results.push({
                    id: 9000 + index, // Temp ID, will be reassigned dynamically in script.js
                    brand: brand,
                    title: title,
                    code: 'GROUPON' + Math.floor(Math.random() * 10000), // Placeholder code
                    discount: "SPECIAL",
                    incentiveText: "Exclusive Deal",
                    incentiveDesc: "Scraped today",
                    description: description,
                    category: "shopping", // Defaulting to shopping
                    rating: 4.8,
                    ratingsCount: Math.floor(Math.random() * 1000) + 100,
                    badge: index < 3 ? "hot" : null,
                    expiry: "Limited time",
                    usesToday: Math.floor(Math.random() * 500) + 50,
                    couponsLeft: Math.floor(Math.random() * 200) + 10,
                    bannerImg: "https://images.unsplash.com/photo-1607082349566-187342175e2f?w=600&h=300&fit=crop",
                    brandLogo: "https://logo.clearbit.com/groupon.com"
                });
            });
            return results;
        });

        console.log(`Scraped ${coupons.length} coupons from Groupon.`);

        if (coupons.length > 0) {
            fs.writeFileSync('groupon.json', JSON.stringify(coupons, null, 2));
            console.log('Saved to groupon.json');
        } else {
            console.log('No coupons found. Site structure might have changed or CAPTCHA blocked the request.');
        }

    } catch (e) {
        console.error('Error during scraping:', e);
    } finally {
        await browser.close();
    }
})();
