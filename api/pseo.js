for (const b of (pseoConfig.brands || [])) {
        if (slug.startsWith(b.slug)) {
            matchedBrand = b;
            const remaining = slug.replace(new RegExp(`^${b.slug}-?`), '');
            matchedIntent = (pseoConfig.intentModifiers || []).find(i => i.slug === remaining)
                || (pseoConfig.intentModifiers ? pseoConfig.intentModifiers[0] : { slug: 'promo-codes', en: 'Promo Codes' });
            break;
        }
    }