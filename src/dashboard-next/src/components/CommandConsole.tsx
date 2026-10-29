
//Mock Data for now, will be replaced with actual data in task 5
const commands = [
    {label: "Restart Core Services"},
    {label: "Reset CAN Interface"},
    {label: "Ping Radio"},
    {label: "Ping LiDAR"},
];

//Mock last result for now, will be replaced with actual data in task 2
const lastLog = "14:32:15 - Ping LiDAR: timeout · exit 1";

export default function CommandConsole(){
    return (
        <footer className="flex flex-wrap items-center gap-x-2.5 gap-y-2 border-t border-line bg-bar px-4 py-2">
            <span className="mr-1.5 text-sm font-semibold">Quick Command Console</span>
                    {commands.map((cmd) => (
                        <button type="button"
                            key={cmd.label}
                            className="cursor-pointer text-sm min-h-11 rounded-lg border border-line bg-page px-3.5">
                            {cmd.label}
                        </button>
                    ))}
            <span className="ml-2 font-mono text-xs text-danger-soft">
                {lastLog}
            </span>
        </footer>
    );
}