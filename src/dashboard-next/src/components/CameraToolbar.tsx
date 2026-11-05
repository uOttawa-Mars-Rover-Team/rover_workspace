type CameraToolbarProps = {
    cameraName: string;
};

const actions = [
    {
        label: "View image",
        icon: (
            <>
                <rect x="3" y="4" width="18" height="16" rx="2" />
                <circle cx="9" cy="10" r="1.5" />
                <path d="M21 16l-5-5-8 9" />
            </>
        ),
    },
    {
        label: "Take picture",
        icon: (
            <>
                <path d="M4 8h3l2-3h6l2 3h3v11H4z" />
                <circle cx="12" cy="13" r="3.5" />
            </>
        ),
    },
    {
        label: "Record video",
        icon: (
            <>
                <rect x="3" y="6" width="13" height="12" rx="2" />
                <path d="M16 10l5-3v10l-5-3" />
            </>
        ),
    },
    {
        label: "Pause feed",
        icon: (
            <>
                <circle cx="12" cy="12" r="9" />
                <path d="M10 9v6M14 9v6" />
            </>
        ),
    },
    {
        label: "Export",
        icon: (
            <>
                <path d="M5 4h7M5 4v16h14v-7" />
                <path d="M13 11l7-7M15 4h5v5" />
            </>
        ),
    },
];

export default function CameraToolbar({ cameraName }: CameraToolbarProps) {
    return (
        <div className="flex flex-wrap items-center border-t border-line px-1">
            {actions.map((action) => (
                <button
                    type="button"
                    key={action.label}
                    aria-label={`${action.label}, ${cameraName}`}
                    className="cursor-pointer flex h-10 w-10 items-center justify-center text-accent"
                >
                    <svg
                        viewBox="0 0 24 24"
                        className="h-4 w-4"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                    >
                        {action.icon}
                    </svg>
                </button>
            ))}
            <button type="button" className="cursor-pointer h-10 px-2 text-xs text-accent">
                Edit
            </button>
            <div className="flex-1" />
            <button type="button" className="cursor-pointer h-10 px-2 text-xs text-ink">
                ROS Details
            </button>
        </div>
    );
}