#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "WebBuildMarker.generated.h"

/** The one C++ class the web (Wasm) build needs. Also lets Blueprints ask whether they run in the browser. */
UCLASS()
class MCPTEST_API UWebBuildMarker : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** True in the web (Wasm) build, false everywhere else. */
	UFUNCTION(BlueprintPure, Category = "Web")
	static bool IsWebBuild();
};
