"routes": [
        { "src": "/api/offers", "dest": "/api/offers.js" },
        { "src": "/api/check", "dest": "/api/check.js" },
        { "src": "/api/postback", "dest": "/api/postback.js" },
        { "src": "/api/admin", "dest": "/api/admin.js" },
        { "src": "/api/download", "dest": "/api/download.js" },
        { "src": "/secretadmin2026here", "dest": "/secretadmin2026here.html" },
        { "src": "/sitemap.xml", "dest": "/api/sitemap.js?index=1" },
        { "src": "/sitemap_([0-9]+)\\.xml", "dest": "/api/sitemap.js?page=$1" },
        { "src": "/(es|fr|pt)/coupons/([^/]+)", "dest": "/api/pseo.js?lang=$1&slug=$2" },
        { "src": "/coupons/([^/]+)", "dest": "/api/pseo.js?lang=en&slug=$1" },
        { "src": "/(.*)", "dest": "/$1" }
    ]