// ============================================
// OGAds Postback Endpoint
// Receives conversion postbacks from OGAds
// ============================================

const completedSessions = global.completedSessions || new Set();
global.completedSessions = completedSessions;

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST');

    const userIP = req.query?.ip
        || req.query?.aff_sub5
        || req.body?.ip
        || req.headers['x-forwarded-for']?.split(',')[0]?.trim()
        || '127.0.0.1';

    const siteId = req.query?.site || req.query?.aff_sub4 || req.query?.sub4 || 'couponfinder';
    const offerId = req.query?.offerid || req.query?.offer_id || 'N/A';
    const payout = req.query?.payout || '0';

    // Mark completed locally in this service
    completedSessions.add(userIP);
    completedSessions.add(siteId + '_' + userIP);

    console.log(`[OGAds Postback] Verified conversion: Site=${siteId}, IP=${userIP}, Offer=${offerId}, Payout=$${payout}`);

    // Multi-site forwarding registry:
    // If you have other landing pages hosted on separate domains, add them here:
    const remoteSites = {
        'matchmasters': 'https://matchmastersmod.vercel.app/api/check',
        'movieunlocker': 'https://movieunlocker.vercel.app/api/check'
    };

    if (remoteSites[siteId]) {
        try {
            await fetch(`${remoteSites[siteId]}?action=postback&ip=${encodeURIComponent(userIP)}&offerid=${encodeURIComponent(offerId)}`);
            console.log(`[OGAds Postback] Forwarded to ${remoteSites[siteId]}`);
        } catch (err) {
            console.error(`[OGAds Postback] Forwarding error:`, err.message);
        }
    }

    return res.status(200).json({
        success: true,
        message: "Conversion postback acknowledged",
        site: siteId,
        ip: userIP
    });
}
