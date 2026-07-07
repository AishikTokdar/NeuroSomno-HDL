if exist('../LICENSE', 'file') || exist('../dataset', 'dir')
    cd('..');
end
c3Files = dir(fullfile('dataset', '*_C3A2.mat'));
X = [];
Y = [];
for k = 1:length(c3Files)
    [~, name, ~] = fileparts(c3Files(k).name);
    subject = name(1:end-5);
    load(fullfile('dataset', sprintf('%s_C3A2.mat', subject)), 'c3_filt');
    load(fullfile('dataset', sprintf('%s_C4A1.mat', subject)), 'c4_filt');
    load(fullfile('dataset', sprintf('%s_label.mat', subject)), 'labels');
    fs = 128;
    winSize = 11 * fs;
    stride = fs;
    N = length(c3_filt);
    numWins = floor((N - winSize) / stride) + 1;
    for i = 1:numWins
        startIdx = (i-1)*stride + 1;
        endIdx = startIdx + winSize - 1;
        c3_win = c3_filt(startIdx:endIdx);
        c4_win = c4_filt(startIdx:endIdx);
        c3_norm = normalize_zscore(c3_win);
        c4_norm = normalize_zscore(c4_win);
        seg = [c3_norm, c4_norm];
        labelIdx = floor(startIdx / fs) + 2;
        if labelIdx > length(labels)
            labelIdx = length(labels);
        end
        lbl = labels(labelIdx);
        X = [X; seg];
        Y = [Y; lbl];
    end
end
numSamples = size(X, 1);
randIdx = randperm(numSamples);
trainCut = floor(0.80 * numSamples);
valCut = trainCut + floor(0.10 * numSamples);
trainIdx = randIdx(1:trainCut);
valIdx = randIdx(trainCut+1:valCut);
testIdx = randIdx(valCut+1:end);
eeg_train = X(trainIdx, :);
train_labels = Y(trainIdx);
eeg_valid = X(valIdx, :);
valid_labels = Y(valIdx);
eeg_test = X(testIdx, :);
test_labels = Y(testIdx);
save('dataset/eeg_train.mat', 'eeg_train');
save('dataset/train_labels.mat', 'train_labels');
save('dataset/eeg_valid.mat', 'eeg_valid');
save('dataset/valid_labels.mat', 'valid_labels');
save('dataset/eeg_test.mat', 'eeg_test');
save('dataset/test_labels.mat', 'test_labels');
