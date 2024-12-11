import os
from pathlib import Path
from typing import List
import logging


class FeatureLoader:
    def __init__(self, bot, features_dir: str = "src/features"):
        self.bot = bot
        self.features_dir = Path(features_dir)
        self.loaded_features: List[str] = []
        self.logger = logging.getLogger(__name__)

    async def load_all_features(self) -> None:
        """Discovers and loads all feature modules in the features directory"""
        if not self.features_dir.exists():
            self.logger.warning(f"Features directory not found: {self.features_dir}")
            return

        # Walk through all python files in features directory
        for root, _, files in os.walk(self.features_dir):
            for file in files:
                # Only process python files
                if file.endswith(".py"):
                    feature_path = Path(root) / file
                    module_path = self._get_module_path(feature_path)

                    try:
                        await self._load_feature(module_path)
                    except Exception as e:
                        self.logger.error(
                            f"Failed to load feature {module_path}: {str(e)}"
                        )

    def _get_module_path(self, feature_path: Path) -> str:
        """Converts file path to module import path"""
        relative_path = feature_path.relative_to(self.features_dir.parent)
        # Convert path to module notation and remove .py
        return str(relative_path).replace(os.sep, ".")[:-3]

    async def _load_feature(self, module_path: str) -> None:
        """Loads a single feature module"""
        try:
            await self.bot.load_extension(module_path)
            self.loaded_features.append(module_path)
            self.logger.info(f"Loaded feature: {module_path}")
        except Exception as e:
            self.logger.error(f"Error loading {module_path}: {str(e)}")
            raise e

    async def reload_all_features(self) -> None:
        """Reloads all currently loaded features"""
        for feature in self.loaded_features.copy():
            try:
                await self.bot.reload_extension(feature)
                self.logger.info(f"Reloaded feature: {feature}")
            except Exception as e:
                self.logger.error(f"Error reloading {feature}: {str(e)}")
                # Remove from loaded features if reload fails
                self.loaded_features.remove(feature)
