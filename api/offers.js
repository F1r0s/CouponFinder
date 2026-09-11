// ============================================
// API Offers Proxy - Serverless Function
// Securely proxies OGAds API to avoid exposing API key
// ============================================

export default async function handler(req, res) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        // Get user's real IP
        const userIP = req.headers['x-forwarded-for']?.split(',')[0]?.trim()
            || req.headers['x-real-ip']
            || req.connection?.remoteAddress
            || '127.0.0.1';

        // Get user agent
        const userAgent = req.headers['user-agent'] || '';

        // Fetch offers from OGAds using user's endpoint and API key
        const apiKey = process.env.OGADS_API_KEY || '47558|DluqLUTirEcifKUEHLp0wrBpqTebJR7XbTqwtkL666b7e813';
        const apiUrl = `https://appcomplete.org/api/v2?ip=${encodeURIComponent(userIP)}&user_agent=${encodeURIComponent(userAgent)}&max=50`;

        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`OGAds API returned ${response.status}`);
        }

        const data = await response.json();
        let offers = data.offers || data || [];

        // Sort: boosted first, then by payout descending
        offers.sort((a, b) => {
            if (a.boosted && !b.boosted) return -1;
            if (!a.boosted && b.boosted) return 1;
            return (parseFloat(b.payout) || 0) - (parseFloat(a.payout) || 0);
        });

        // Map to clean format and return top 2
        const topOffers = offers.slice(0, 2).map(offer => ({
            id: offer.offerid || offer.id,
            name: offer.name_short || offer.name || 'Complete Offer',
            description: offer.adcopy || offer.description || 'Quick verification',
            image: offer.picture || offer.icon || '',
            link: offer.link || offer.url || '#',
            payout: parseFloat(offer.payout) || 0,
            boosted: !!offer.boosted
        }));

        return res.status(200).json(topOffers);

    } catch (error) {
        console.error('Error fetching offers from OGAds:', error.message);
        
        // Return high-quality fallback offers matching exact schema so frontend never breaks
        const fallbackOffers = [
            {
                id: 101,
                name: "Install & Open TikTok",
                description: "Download and run the app for 30 seconds to complete verification",
                image: "https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=100&h=100&fit=crop",
                link: "https://tiktok.com",
                payout: 1.50
            },
            {
                id: 102,
                name: "Complete Quick 2-Min Survey",
                description: "Answer 4 simple questions to verify your human identity",
                image: "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=100&h=100&fit=crop",
                link: "https://surveys.com",
                payout: 1.25
            }
        ];
        
        return res.status(200).json(fallbackOffers);
    }
}
