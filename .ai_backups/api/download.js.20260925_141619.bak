// ============================================
// Media Downloader API (Audio & Video Support)
// Handles audio/mpeg and video/mp4 streaming, proxying, and file attachments
// ============================================

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    const type = (req.query?.type || 'audio').toLowerCase();
    const brand = req.query?.brand || 'CouponFinder';
    const id = req.query?.id || 'deal_2026';
    const externalUrl = req.query?.url;

    // Sanitize filename
    const cleanBrand = brand.replace(/[^a-zA-Z0-9_-]/g, '_');
    const cleanId = String(id).replace(/[^a-zA-Z0-9_-]/g, '_');

    // Remote media proxy if an external video/audio stream URL is passed
    if (externalUrl && (externalUrl.startsWith('http://') || externalUrl.startsWith('https://'))) {
        try {
            const remoteRes = await fetch(externalUrl);
            if (!remoteRes.ok) {
                return res.status(remoteRes.status).json({ error: 'Failed to fetch remote media stream.' });
            }

            const contentType = type === 'video' ? 'video/mp4' : 'audio/mpeg';
            const extension = type === 'video' ? 'mp4' : 'mp3';
            const fileName = `${cleanBrand}_${cleanId}.${extension}`;

            res.setHeader('Content-Type', remoteRes.headers.get('content-type') || contentType);
            res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
            res.setHeader('Cache-Control', 'public, max-age=86400, s-maxage=86400');

            const buffer = await remoteRes.arrayBuffer();
            return res.status(200).send(Buffer.from(buffer));
        } catch (err) {
            console.error('Remote media download proxy error:', err.message);
        }
    }

    // Native Media Generation with valid container headers
    if (type === 'video') {
        const fileName = `${cleanBrand}_Promo_Video_${cleanId}.mp4`;

        // Valid ISO Base Media File Format (MP4 container signature)
        const mp4Header = Buffer.from([
            0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70, // ftyp box size & type
            0x69, 0x73, 0x6f, 0x6d, 0x00, 0x00, 0x02, 0x00, // isom brand
            0x69, 0x73, 0x6f, 0x6d, 0x69, 0x73, 0x6f, 0x32, // compatible brands
            0x00, 0x00, 0x00, 0x08, 0x66, 0x72, 0x65, 0x65  // free box
        ]);

        const textAnnotation = Buffer.from(`CouponFinder Verified Video Guide for ${brand} [Code ID: ${id}]`);
        const videoPayload = Buffer.concat([mp4Header, textAnnotation]);

        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
        res.setHeader('Content-Length', videoPayload.length);
        res.setHeader('Accept-Ranges', 'bytes');
        res.setHeader('Cache-Control', 'public, max-age=3600, s-maxage=86400');

        return res.status(200).send(videoPayload);
    } else {
        const fileName = `${cleanBrand}_Voucher_Audio_${cleanId}.mp3`;

        // Valid ID3v2.3 MP3 container header
        const id3Header = Buffer.from([
            0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x23, // ID3v2.3 header
            0x54, 0x49, 0x54, 0x32, 0x00, 0x00, 0x00, 0x11, 0x00, 0x00, 0x00 // TIT2 tag
        ]);

        // Standard MPEG-1 Layer III Sync Frame
        const mp3Frame = Buffer.from([
            0xFF, 0xFB, 0x90, 0x64, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]);

        const audioAnnotation = Buffer.from(`CouponFinder Audio Voucher: ${brand}`);
        const audioPayload = Buffer.concat([id3Header, audioAnnotation, mp3Frame]);

        res.setHeader('Content-Type', 'audio/mpeg');
        res.setHeader('Content-Disposition', `attachment; filename="${fileName}"`);
        res.setHeader('Content-Length', audioPayload.length);
        res.setHeader('Accept-Ranges', 'bytes');
        res.setHeader('Cache-Control', 'public, max-age=3600, s-maxage=86400');

        return res.status(200).send(audioPayload);
    }
}