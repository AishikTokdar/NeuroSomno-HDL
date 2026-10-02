function normalized = normalize_zscore(X)
    assert(all(isfinite(X(:))), 'Signal must be finite');
    scale = std(X, 1);
    if scale == 0
        normalized = X - mean(X);
    else
        normalized = (X - mean(X)) ./ scale;
    end
end
