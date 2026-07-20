if exist('../LICENSE', 'file') || exist('../dataset', 'dir')
    cd('..');
end
load('dataset/eeg_train.mat', 'eeg_train');
load('dataset/train_labels.mat', 'train_labels');
X_0 = eeg_train(train_labels == 0, :);
X_1 = eeg_train(train_labels == 1, :);
n0 = size(X_0, 1);
n1 = size(X_1, 1);
if n1 < n0
    diff = n0 - n1;
    X_synthetic = zeros(diff, size(eeg_train, 2));
    k = 5;
    for i = 1:diff
        idx = randi(n1);
        sample = X_1(idx, :);
        dists = sum((X_1 - sample).^2, 2);
        [~, sortedIdx] = sort(dists);
        neighborIdx = sortedIdx(randi([2, min(k+1, n1)]));
        neighbor = X_1(neighborIdx, :);
        X_synthetic(i, :) = sample + rand() * (neighbor - sample);
    end
    eeg_train = [X_0; X_1; X_synthetic];
    train_labels = [zeros(n0, 1); ones(n1, 1); ones(diff, 1)];
end
save('dataset/eeg_train_balanced.mat', 'eeg_train');
save('dataset/train_labels_balanced.mat', 'train_labels');
