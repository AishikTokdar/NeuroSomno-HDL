if exist('../LICENSE', 'file') || exist('../dataset', 'dir')
    cd('..');
end
addpath(fullfile(pwd, 'matlab_preprocessing'));
if ~exist('dataset', 'dir')
    mkdir('dataset');
end
edfFiles = dir(fullfile('dataset', '*.edf'));
if isempty(edfFiles)
    disp('SYNTHETIC smoke data; not clinical validation');
    rng(42);
    fs = 128;
    duration = 600;
    t = 0:1/fs:duration-1/fs;
    for k = 1:3
        c3_raw = sin(2*pi*10*t) + 0.5*sin(2*pi*2*t) + 0.1*randn(size(t));
        c4_raw = sin(2*pi*10*t + pi/4) + 0.5*sin(2*pi*2*t) + 0.1*randn(size(t));
        labels = zeros(duration, 1);
        for idx = 60:120:duration-30
            c3_raw(idx*fs+1 : (idx+30)*fs) = 0.1*randn(1, 30*fs);
            c4_raw(idx*fs+1 : (idx+30)*fs) = 0.1*randn(1, 30*fs);
            labels(idx+1 : idx+30) = 1;
        end
        [bn, an] = iirnotch(50/(fs/2), (50/(fs/2))/35);
        [bb, ab] = butter(4, [0.5 45]/(fs/2), 'bandpass');
        c3_filt = filtfilt(bb, ab, filtfilt(bn, an, c3_raw));
        c4_filt = filtfilt(bb, ab, filtfilt(bn, an, c4_raw));
        save(sprintf('dataset/ucddb00%d_C3A2.mat', k), 'c3_filt');
        save(sprintf('dataset/ucddb00%d_C4A1.mat', k), 'c4_filt');
        save(sprintf('dataset/ucddb00%d_label.mat', k), 'labels');
    end
else
    for k = 1:length(edfFiles)
        filename = fullfile('dataset', edfFiles(k).name);
        [~, name, ~] = fileparts(filename);
        data = edfread(filename);
        fs = 128;
        [c3_data, c4_data, rates] = extract_channels(data, edfinfo(filename));
        [p3,q3] = rat(fs/rates(1)); [p4,q4] = rat(fs/rates(2));
        c3_data = resample(c3_data, p3, q3); c4_data = resample(c4_data, p4, q4);
        assert(length(c3_data)==length(c4_data), 'Channel lengths disagree');
        wo = 50/(fs/2);
        bw = wo/35;
        [b_notch, a_notch] = iirnotch(wo, bw);
        c3_notch = filtfilt(b_notch, a_notch, c3_data);
        c4_notch = filtfilt(b_notch, a_notch, c4_data);
        [b_bp, a_bp] = butter(4, [0.5, 45]/(fs/2), 'bandpass');
        c3_filt = filtfilt(b_bp, a_bp, c3_notch);
        c4_filt = filtfilt(b_bp, a_bp, c4_notch);
        save(sprintf('dataset/%s_C3A2.mat', name), 'c3_filt');
        save(sprintf('dataset/%s_C4A1.mat', name), 'c4_filt');
        label_file = fullfile('dataset', sprintf('%s_label.mat', name));
        if exist(label_file, 'file')
            load(label_file, 'labels');
            assert(numel(labels)==floor(numel(c3_filt)/fs) && all(ismember(labels,[0 1])), 'One binary label per second required');
        else
            error('Missing required annotations: %s', label_file);
        end
    end
end
