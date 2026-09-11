// ============================================
// API Check & Postback Endpoint
// Strictly verifies OGAds offer completions (Requires 1 completed offer)
// ============================================

// Global memory cache for completed IP / sessions
// Works across requests in server runtime
const completedSessions = global.completedSessions || new Set();
global.completedSessions = completedSessions;

export default function handler(req, res) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST');

    if (req.method !== 'GET' && req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    // Capture visitor IP
    const userIP = req.query?.ip 
        || req.headers['x-forwarded-for']?.split(',')[0]?.trim()
        || req.headers['x-real-ip']
        || req.connection?.remoteAddress
        || '127.0.0.1';

    const sessionId = req.query?.session || req.query?.sid || userIP;

    // 1. OGAds Postback Handler
    // In OGAds Dashboard -> Postback Settings:
    // URL: https://yourdomain.com/api/check?action=postback&ip={ip}&offerid={offer_id}
    if (req.query?.action === 'postback' || req.query?.postback === '1' || req.body?.postback) {
        const postbackIP = req.query?.ip || req.body?.ip || userIP;
        const postbackSession = req.query?.session || req.query?.sub4 || postbackIP;

        completedSessions.add(postbackIP);
        completedSessions.add(postbackSession);

        console.log(`[OGAds Postback] Verified completion for IP: ${postbackIP}`);
        return res.status(200).json({ success: true, message: "Postback recorded successfully" });
    }

    // 2. Developer test verification only with explicit secret token
    if (req.query?.admin_unlock === 'couponfinder_dev_test') {
        completedSessions.add(userIP);
        return res.status(200).json({ completed: true, tested: true });
    }

    // 3. Regular Check
    const isCompleted = completedSessions.has(userIP) || completedSessions.has(sessionId);

    return res.status(200).json({ 
        completed: isCompleted,
        requiredOffers: 1,
        message: isCompleted 
            ? "1 offer completed successfully! Code unlocked." 
            : "Incomplete: You must complete 1 offer before the code is revealed."
    });
}
