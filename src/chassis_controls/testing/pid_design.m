clc;
syms t positive;

FL_coeffs = [0.27291033895945316 -1.295702995675999];
FR_coeffs = [0.2730788189594534 -1.3075589956760272];
RR_coeffs = [0.28206923374321247 -1.5866751633510998];
RL_coeffs = [0.27404910467374133 -1.528822567105082];

% FLp = piecewise( ...
%     subs(poly2sym(FL_coeffs, t), t, t) < 0, 0, ...
%     t <= 100, poly2sym(FL_coeffs, t), ...
%     t > 100, subs(poly2sym(FL_coeffs, t), t, 100));

curve = poly2sym(RR_coeffs, t);
roots = solve(curve,t,"MaxDegree",3,"Real",true);
deadband = vpa(min(roots(roots>0)),8);
pwm_domain = heaviside(t-deadband)*(curve) - (curve-subs(curve,t,100))*heaviside(t-100);

pwm_domain_approx = series(pwm_domain,t, 50, 'Direction', 'realAxis');
fplot([pwm_domain pwm_domain_approx], [-5, 105]);
legend("Curve fit with clamp", "puiseux series expansion (linearization)");
xlabel = "PWM [%]";
ylabel = "Velocity [rad/s]";
title('Velocity v. PWM');

freq_domain = laplace(pwm_domain_approx);
[freq_num, freq_den] = numden(freq_domain);
freq_num = double(sym2poly(freq_num));
freq_den = double(sym2poly(freq_den));
Ps = tf(freq_num, freq_den)

C1 = pidtune(Ps,'PI');
C2 = pidtune(Ps,'PID');
Ts1 = feedback(Ps*C1, 1);
Ts2 = feedback(Ps*C2, 1);
step(Ts1, Ts2);
legend('PI','PID','Location','SouthEast')

% PEqn = P(s) == laplace(pwm_domain)*(1/s);
% p(t) = ilaplace(rhs(PEqn));
% fplot(@(t) p(t), [0 150]);
% grid on;
% xlabel('Time, t');
% ylabel('p(t)');

% Kp = 300;
% Ki = 0;
% Kd = 10;
% Ps = 1/(s^2+10*s+20);
% Cs = pid(Kp, Ki, Kd);
% Ts = feedback(Cs*Ps,1)
% t = 0:0.01:2;
% step(Ts,t)
