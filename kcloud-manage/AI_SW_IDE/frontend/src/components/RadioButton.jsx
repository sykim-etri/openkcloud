
export function Radio({ onSelect }) {
    return (
        <div class="flex gap-10">
        <div class="inline-flex items-center">
            <label class="relative flex items-center cursor-pointer" for="html-custom-icon">
            <input
                name="framework-custom-icon"
                type="radio"
                class="peer h-5 w-5 cursor-pointer appearance-none rounded-full border border-slate-300 checked:border-slate-800 transition-all"
                id="html-custom-icon"
                checked
            />
            <span class="absolute w-3 h-3 rounded-full opacity-0 peer-checked:opacity-100 transition-opacity duration-200 top-2 left-2 transform -translate-x-1/2 -translate-y-1/2">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="w-4 h-4">
                <path d="M2 6.342a3.375 3.375 0 0 1 6-2.088 3.375 3.375 0 0 1 5.997 2.26c-.063 2.134-1.618 3.76-2.955 4.784a14.437 14.437 0 0 1-2.676 1.61c-.02.01-.038.017-.05.022l-.014.006-.004.002h-.002a.75.75 0 0 1-.592.001h-.002l-.004-.003-.015-.006a5.528 5.528 0 0 1-.232-.107 14.395 14.395 0 0 1-2.535-1.557C3.564 10.22 1.999 8.558 1.999 6.38L2 6.342Z" />
                </svg>
            </span>
            </label>
            <label class="ml-2 text-slate-600 cursor-pointer text-sm" for="html-custom-icon">
            HTML
            </label>
        </div>
        
        <div class="inline-flex items-center">
            <label class="relative flex items-center cursor-pointer" for="react-custom-icon">
            <input
                name="framework-custom-icon"
                type="radio"
                class="peer h-5 w-5 cursor-pointer appearance-none rounded-full border border-slate-300 checked:border-slate-800 transition-all"
                id="react-custom-icon"
            />
            <span class="absolute w-3 h-3 rounded-full opacity-0 peer-checked:opacity-100 transition-opacity duration-200 top-2 left-2 transform -translate-x-1/2 -translate-y-1/2">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="w-4 h-4">
                <path d="M2 6.342a3.375 3.375 0 0 1 6-2.088 3.375 3.375 0 0 1 5.997 2.26c-.063 2.134-1.618 3.76-2.955 4.784a14.437 14.437 0 0 1-2.676 1.61c-.02.01-.038.017-.05.022l-.014.006-.004.002h-.002a.75.75 0 0 1-.592.001h-.002l-.004-.003-.015-.006a5.528 5.528 0 0 1-.232-.107 14.395 14.395 0 0 1-2.535-1.557C3.564 10.22 1.999 8.558 1.999 6.38L2 6.342Z" />
                </svg>
            </span>
            </label>
            <label class="ml-2 text-slate-600 cursor-pointer text-sm" for="react-custom-icon">
            React
            </label>
        </div>
        </div>
  );
}


export default Radio;