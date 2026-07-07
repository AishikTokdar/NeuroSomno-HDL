function X_norm = normalize_zscore(X)
    X_norm = (X - mean(X)) ./ std(X);
end
