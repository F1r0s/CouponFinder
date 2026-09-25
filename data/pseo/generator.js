const brandVariants = config.brands.flatMap(brand => {
    return [brand, ...config.brandVariations[brand] || []];
  });