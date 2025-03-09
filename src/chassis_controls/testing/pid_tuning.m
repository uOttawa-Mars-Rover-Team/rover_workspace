clear all;

table = readtable("src/chassis_controls/testing/wheel_data.csv");
wheel_data = table2struct(table);

plants = cell(1, 4);
for i=1 : length(wheel_data)
    num = str2num(wheel_data(i).tf_num);
    den = str2num(wheel_data(i).tf_den);
    plants{i} = tf(num, den);
end

FL = plants{1};
pidTuner(FL)
FR = plants{2};
pidTuner(FR)
RR = plants{3};
pidTuner(RR)
RL = plants{4};
pidTuner(RL)

