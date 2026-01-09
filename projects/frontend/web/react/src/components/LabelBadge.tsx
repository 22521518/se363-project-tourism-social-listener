import { HelpCircle, Plane, MapPin, Smile } from "lucide-react";

const TYPE_ICONS: Record<
  "intention" | "traveling_type" | "location" | "sentiment",
  any
> = {
  intention: HelpCircle,
  traveling_type: Plane,
  location: MapPin,
  sentiment: Smile,
};

export default function LabelBadge({
  type,
  label,
  color,
}: {
  type: "traveling_type" | "intention" | "location" | "sentiment";
  label: string;
  color: string;
}) {
  const Icon = TYPE_ICONS[type];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium`}
      style={{
        backgroundColor: color,
        color: "white",
      }}
    >
      <Icon size={12} />
      {label}
    </span>
  );
}
