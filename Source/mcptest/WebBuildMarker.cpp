#include "WebBuildMarker.h"

bool UWebBuildMarker::IsWebBuild()
{
#if defined(PLATFORM_WASM) && PLATFORM_WASM
	return true;
#else
	return false;
#endif
}
